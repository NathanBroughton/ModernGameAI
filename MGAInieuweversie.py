# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 19:14:58 2022

@author: NatBr
"""

import botbowl
from botbowl.core import Action, game
import numpy as np
import copy
import time
from botbowl.web import server
import MCTS_opp as opp

rollout_depth = 10
tree_depth = 5
n_simulations = 100

if rollout_depth == None:
    rollout2terminal = True
else:
    rollout2terminal = False

if tree_depth == None:
    tree2terminal = True
else:
    tree2terminal = False


class MyRandomBot(botbowl.Agent):
    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        self.rnd = np.random.RandomState(seed)

    def new_game(self, team):
        self.my_team = team

    def act(self, game):
        # Select a random action type
        while True:
            action_choice = self.rnd.choice(game.state.available_actions)
            # Ignore PLACE_PLAYER actions
            if action_choice.action_type != botbowl.ActionType.PLACE_PLAYER:
                break

        # Select a random position and/or player
        position = self.rnd.choice(action_choice.positions) if len(
            action_choice.positions) > 0 else None
        player = self.rnd.choice(action_choice.players) if len(
            action_choice.players) > 0 else None

        # Make action object
        action = botbowl.Action(action_choice.action_type,
                                position=position, player=player)

        # Return action to the framework
        return action

    def end_game(self, game):
        pass


class MCTSNode:
    # This node is used for the recursive tree search
    def __init__(self, action=None, parent=None):
        self.parent = parent
        self.action = action
        self.children = []
        self.child_actions = []
        self.evaluations = []
        self.terminal = False
        self.fully_expanded = False

    def q(self):
        return np.mean(self.evaluations)

    def n(self):
        return len(self.evaluations)

    def visit(self, score):
        self.evaluations.append(score)

    def backpropagate(self, score):
        self.visit(score)
        if self.parent != None:
            self.parent.backpropagate(score)

    def expand(self, action):
        child = MCTSNode(action=action, parent=self)
        self.children.append(child)
        self.child_actions.append(action)
        return child

    def is_terminal(self):
        return self.terminal

    def is_fully_expanded(self):
        return self.fully_expanded

    def best_child(self, c_val=0.1):
        ucb_values = []
        for child in self.children:
            ucb_values.append(child.q() / child.n() + c_val *
                              np.sqrt((2 * np.log(self.n()) / child.n())))
        return self.children[np.argmax(ucb_values)]

    def best_action(self, c_val=0.1):
        child = self.best_child(c_val)
        return child.action


class MCTSbot(botbowl.Agent):
    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        self.coin = "heads"
        self.KR = "kick"
        self.rnd = np.random.RandomState(seed)
        self.m = 1
        self.formation = False
        self.off_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "x"],
            ["-", "-", "-", "p", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "s"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "x", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"]
        ]

        self.def_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "S", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "x", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "0"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "S", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"]
        ]
        self.off_formation = botbowl.Formation("Wedge offense", self.off_formation)
        self.def_formation = botbowl.Formation("Zone defense", self.def_formation)
        self.setup_actions = []
        self.no_actions_taken = 0
        self.avg_time = 0

    def new_game(self, game, team):
        self.my_team = team

    def act(self, game):
        ##Scripted coin flip
        if (game.state.available_actions[0].action_type == botbowl.ActionType.HEADS):
            if(self.coin == "heads"):
                action = botbowl.Action(game.state.available_actions[0].action_type)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type)

        ##Scripted kick/receive
        elif(game.state.available_actions[0].action_type == botbowl.ActionType.KICK):
            if(self.KR == "kick"):
                action = botbowl.Action(game.state.available_actions[0].action_type)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type)

        ##Scripted Formation
        # Place a player according to the formation when your team does't have 5 players in a position
        elif(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_PLAYER):
            if (self.formation == False) or (self.formation == True and len(self.setup_actions) != 0):
                action = self.setup(game)
            elif [player.position != None for player in self.my_team.players].count(True) == 5:
                action = botbowl.Action(game.state.available_actions[1].action_type)

            if(action.action_type == botbowl.ActionType.END_SETUP):
                self.formation = False

        elif(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_BALL):
            position = self.rnd.choice(game.state.available_actions[0].positions)
            action = botbowl.Action(game.state.available_actions[0].action_type, position=position)

        ##Stuur deepcopy naar MCTS class om beste actie te kiezen
        else:
            # Time MCTS
            time_start = time.time()
            game_copy = copy.deepcopy(game)
            game_copy.enable_forward_model()
            game_copy.home_agent.human = True
            game_copy.away_agent.human = True

            # Create root node
            root_node = MCTSNode()
            root_step = game_copy.get_step()

            # print("Simulating {0} games".format(n_simulations))
            for i in range(n_simulations):
                # Find a leaf node
                leaf_node, game_copy = self.traverse(root_node, game_copy)
                # Rollout until depth reached or terminal node
                game_copy = self.rollout(game_copy)
                # Evaluate rollout result
                score = self.evaluate(game_copy)
                # Backprop score
                leaf_node.backpropagate(score)
                # Reset to root node
                game_copy.revert(root_step)

            # Select best action
            best_action = root_node.best_action(c_val=0.)

            time_end = time.time()
            print("Found best action:", best_action,
                "in {0} seconds".format(time_end - time_start))
            action = best_action
            self.no_actions_taken += 1
            self.avg_time += (time_end - time_start)
        return action

    def traverse(self, root_node, game_copy):
        # The goal of this function is to find a leaf node (either terminal, unexplored or at max depth)
        current_node = root_node
        if not tree2terminal:
            # We will traverse until either depth reached or terminal
            terminal = False
            traversed_depth = 0
            while not terminal and traversed_depth < tree_depth:
                # Start traversing
                if current_node.fully_expanded:
                    # If already fully expanded, move down the tree
                    current_node = current_node.best_child()
                    traversed_depth += 1

                    # Unless the current node is terminal, we return current node as leaf
                    terminal = current_node.terminal
                    if terminal:
                        return current_node, game_copy

                else:
                    # Retrieve all possible actions
                    possible_action_choices = game_copy.get_available_actions()

                    # Skip until we can play
                    while not game_copy.state.game_over and len(possible_action_choices) == 0:
                        game_copy.step()
                        possible_action_choices = game_copy.get_available_actions()

                    # If we are game over, terminate traversal and return the terminal node and game copy
                    if game_copy.state.game_over:
                        current_node.terminal = True
                        terminal = True
                        return current_node, game_copy

                    # No game over and we can play again, so let's select an action
                    action = self.selection(
                        current_node, possible_action_choices)

                    # Check if the node is actually fully expanded
                    if action == None:
                        current_node.fully_expanded = True
                        current_node = current_node.best_child()
                        traversed_depth += 1

                    # Else we perform the selected action and expand the tree
                    else:
                        game_copy.step(action)
                        current_node = current_node.expand(action)
                        return current_node, game_copy

        else:
            print("Running tree until termination is not yet supported")

    def selection(self, node, possible_action_choices):
        # Select an unexplored random action (and thus a child node), returns None if fully expanded
        actions = []
        for action_choice in possible_action_choices:
            if action_choice.action_type == botbowl.ActionType.PLACE_PLAYER:
                continue
            for player in action_choice.players:
                actions.append(
                    Action(action_choice.action_type, player=player))
            for position in action_choice.positions:
                actions.append(
                    Action(action_choice.action_type, position=position))
            if len(action_choice.players) == len(action_choice.positions) == 0:
                actions.append(Action(action_choice.action_type))

        self.rnd.shuffle(actions)
        for a in actions:
            if a not in node.child_actions:
                return a
        return None

    def rollout(self, game_copy):
        # Perform rollout until game over or target depth is reached
        game_over = False
        rollout_i = 0
        while not game_over and rollout_i < rollout_depth:
            actions = []
            #print("Options:",game_copy.get_available_actions())
            for action_choice in game_copy.get_available_actions():
                if action_choice.action_type == botbowl.ActionType.PLACE_PLAYER:
                    continue
                for player in action_choice.players:
                    actions.append(
                        Action(action_choice.action_type, player=player))
                for position in action_choice.positions:
                    actions.append(
                        Action(action_choice.action_type, position=position))
                if len(action_choice.players) == len(action_choice.positions) == 0:
                    actions.append(Action(action_choice.action_type))
            if(len(actions) != 0):
                a = self.rnd.choice(actions)
                game_copy.step(a)
            rollout_i += 1
            if game_copy.state.game_over:
                game_over = True
        return game_copy

    def evaluate(self, game_copy):
        # Evaluate based on heuristics such as living teammates, whether team has ball and where the ball is on the field
        ball_carrier = game_copy.get_ball_carrier()
        target_x = game_copy.get_opp_endzone_x(self.my_team)
        score = (game_copy.state.home_team.state.score -
                 game_copy.state.away_team.state.score) * 100

        # Score reduction when the ball is far away from the end zone
        if game_copy.get_ball_position() != None:
            x_ball = game_copy.get_ball_position().x
            y_ball = game_copy.get_ball_position().y
            distance2endzone = abs(target_x - x_ball)
            score -= distance2endzone
        else:
            x_ball, y_ball = None, None

        # Increase score if your team is standing and has the ball
        for player in self.my_team.players:
            if player.state.up and not player.state.stunned:
                score += 1
            if player == ball_carrier or game_copy.has_ball(player):
                score += 5 + player.get_ma()
            if x_ball != None and player.position != None:
                player_x = player.position.x
                player_y = player.position.y
                dist = np.linalg.norm(np.array([player_x, player_y]) - np.array([x_ball, y_ball]))
                score -= (dist / player.get_ma())

        enemy_players = game_copy.get_opp_team(self.my_team)
        for player in enemy_players:
            # Increase score when the other team has downed players
            if not player.state.up or player.state.stunned:
                score += 10
            # Reduce score when the opponent has the ball
            if player == ball_carrier or game_copy.has_ball(player):
                score -= 5

        return score

    def setup(self, game):
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)

        # Get the first action if a formation and their actions have been set
        if self.setup_actions:
            action = self.setup_actions.pop(0)

        # If no formation was set, create the actions now and return the first action
        elif not self.setup_actions and self.formation == False:
            if game.get_receiving_team() == self.my_team:
                self.setup_actions = self.off_formation.actions(game, self.my_team)
                self.setup_actions.append(botbowl.Action(botbowl.ActionType.END_SETUP))
                self.formation = True
                action = self.setup_actions.pop(0)

            else:
                self.setup_actions = self.def_formation.actions(game, self.my_team)
                self.setup_actions.append(botbowl.Action(botbowl.ActionType.END_SETUP))
                self.formation = True
                action = self.setup_actions.pop(0)
        return(action)

    def end_game(self, game):
        print("The average time per action taken is", self.avg_time/self.no_actions_taken, "seconds")
        pass


# Register the bot to the framework
botbowl.register_bot('my-random-bot', MyRandomBot)
botbowl.register_bot('MCTS-bot', MCTSbot)
botbowl.register_bot('MCTS-bot_opp', opp.MCTSbot_opp)
#server.start_server(debug=True, use_reloader=False)

if __name__ == "__main__":
    # Load configurations, rules, arena and teams
    config = botbowl.load_config("web")
    ruleset = botbowl.load_rule_set(config.ruleset)
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)
    config.competition_mode = False
    config.debug_mode = False

    # Play 3 games
    game_times = []
    MCTS_wins = 0
    for i in range(3):
        time_startGame = time.time()
        away_agent = botbowl.make_bot("my-random-bot")
        home_agent = botbowl.make_bot('MCTS-bot_opp')

        game = botbowl.Game(i, home, away, home_agent,
                            away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True

        print("Starting game", (i+1))
        game.init()
        if(game.get_winner() == home_agent):
            print("Home team wins!!")
            MCTS_wins += 1
        if(game.get_winner() == away_agent):
            print("Away teams wins!!")
        print(game.get_winner())
        time_endGame = time.time()
        print("Total time of game was: {0} seconds".format(time_endGame - time_startGame))
        print(game.state.home_team.state.score, "-", game.state.away_team.state.score)
        print("Game is over")
    print("Agent won a total of", MCTS_wins, "games")

