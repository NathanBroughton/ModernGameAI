import botbowl
from botbowl.core import Action
import numpy as np
import copy

"""
Deze parameters hieronder zijn hyperparameters voor de MCTS.
Als ze op None staan gaat de rollout/tree search door totdat deze een terminal state heeft bereikt.
Voor nu even op 10 laten staan denk ik, anders duurt het miss te lang om te runnen.
"""

rollout_depth = 10
tree_depth = 10
n_simulations = 1000

if rollout_depth == None:
    rollout2terminal = True
else:
    rollout2terminal = False

if tree_depth == None:
    tree2terminal = True
else:
    tree2terminal = False


# MCTSNode is part of the full tree and keeps track of its own parents, children and game copy
class MCTSNode:
    def __init__(self, game, parent=None, action=None, my_team=None):
        # Set self parameters and copy the game
        self.game_copy = copy.deepcopy(game)
        self.parent = parent
        self.action = action
        self.my_team = my_team

        # self.step is used for traversing different actions
        self.step = self.game_copy.get_step()
        self.children = []
        self.evaluations = []

        # The untried actions keeps track of the leftover available actions
        self.untried_actions = self.game_copy.get_available_actions()

    def num_visits(self):
        return len(self.evaluations)
    
    def visit(self, score):
        self.evaluations.append(score)
    
    def is_terminal(self):
        return self.game_copy.state.game_over

    def backpropagate(self, score):
        # Backpropagate the score to all parents
        self.visit(score)
        if self.parent != None:
            self.parent.backpropagate(score)
    
    def expand(self):
        """
        Both expansion and selection take place in this step. Rather than adding one child node,
        all possible child nodes are added in this function.

        A still occurring problem is that the possible actions are not all legal in the game copy.
        Not sure why, I tried to fix it by performing _is_action_allowed but that doesn't seem to work :()
        """
        if len(self.untried_actions) != 0:
            for action_choice in self.untried_actions:
                for player in action_choice.players:
                    action = Action(action_choice.action_type, player=player)
                    if self.game_copy._is_action_allowed(action):
                        self.game_copy.step(action)
                        child = MCTSNode(self.game_copy, parent=self, action=action, my_team=self.my_team)
                        self.children.append(child)
                        self.game_copy.revert(self.step)
                
                for position in action_choice.positions:
                    action = Action(action_choice.action_type, position=position)
                    if self.game_copy._is_action_allowed(action):
                        self.game_copy.step(action)
                        child = MCTSNode(self.game_copy, parent=self, action=action, my_team=self.my_team)
                        self.children.append(child)
                        self.game_copy.revert(self.step)

                if len(action_choice.players) == len(action_choice.positions) == 0:
                    action = Action(action_choice.action_type)
                    if self.game_copy._is_action_allowed(action):
                        self.game_copy.step(action)
                        child = MCTSNode(self.game_copy, parent=self, action=action, my_team=self.my_team)
                        self.children.append(child)
                        self.game_copy.revert(self.step)

            self.untried_actions = []

    def rollout_policy(self, moves):
        # Not sure if correct, copied from MGAIAssignment2
        return moves[np.random.randint(len(moves))]

    def rollout(self):
        self.game_copy.revert(self.step)
        # Either run until terminal or rollout depth is reached
        if rollout2terminal:
            go = self.game_copy.state.game_over
            while not go:
                moves = self.game_copy.state.available_actions
                if len(moves) == 0:
                    go = True
                    break
                action = self.rollout_policy(moves)
                self.game_copy.step(action)
                go = self.game_copy.state.game_over
            score = self.evaluate()
        else:
            for i in range(rollout_depth):
                go = self.game_copy.state.game_over
                moves = self.game_copy.state.available_actions
                if len(moves) == 0 or go:
                    break
                action = self.rollout_policy(moves)
                self.game_copy.step(action)
            score = self.evaluate()
        
        return score

    def evaluate(self):
        # Copied from MGAIAssignment 2
        ball_carrier = self.game_copy.get_ball_carrier()
        target_x = self.game_copy.get_opp_endzone_x(self.my_team)
        score = (self.game_copy.state.home_team.state.score - self.game_copy.state.away_team.state.score) * 100
        for player in self.my_team.players:
            if player.state.up and not player.state.stunned:
                score += 1
            if player == ball_carrier or self.game_copy.has_ball(player):
                # Not sure which conditional to use, so why not use both
                score += 5 + player.get_ma()
        if self.game_copy.get_ball_position() != None:
            x_ball = self.game_copy.get_ball_position().x
            distance2endzone = abs(target_x - x_ball)
            score -= distance2endzone
        return score

    def best_child(self, c_value=0.1):
        # Copied from MCTS implementation
        choices_weights = [(np.sum(c.evaluations) / c.num_visits()) + c_value * np.sqrt((2 * np.log(self.num_visits()) / c.num_visits())) for c in self.children]
        return self.children[np.argmax(choices_weights)]
    
class MCTSbot(botbowl.Agent):
    # Copied from search_example.py
    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        self.rnd = np.random.RandomState(seed)
    
    def new_game(self, game, team):
        self.my_team = team

    def tree_policy(self, root_node):
        # Copied from MCTS implementation
        current_node = root_node
        if tree2terminal:
            while not current_node.is_terminal():
                if len(current_node.untried_actions) != 0:
                    current_node.expand()
                else:
                    current_node = current_node.best_child()
        else:
            i_tree = 0
            while i_tree < tree_depth:
                if len(current_node.untried_actions) != 0:
                    current_node.expand()
                else:
                    current_node = current_node.best_child()
                    i_tree += 1
        return current_node

    def act(self, game):
        # Copied from search_example and adapted to MCTS
        game_copy = copy.deepcopy(game)
        game_copy.enable_forward_model()
        game_copy.home_agent.human = True
        game_copy.away_agent.human = True
        
        # root_step = game_copy.get_step()

        root_node = MCTSNode(game=game_copy, my_team=self.my_team)
        for i in range(n_simulations):
            v = self.tree_policy(root_node)
            reward = v.rollout()
            v.backpropagate(reward)

        return root_node.best_child(c_value=0).action

    def end_game(self, game):
        pass
        

# Standard botbowl call

# Register the bot to the framework
botbowl.register_bot('search-bot', MCTSbot)

# Load configurations, rules, arena and teams
config = botbowl.load_config("bot-bowl")
ruleset = botbowl.load_rule_set(config.ruleset)
arena = botbowl.load_arena(config.arena)
home = botbowl.load_team_by_filename("human", ruleset)
away = botbowl.load_team_by_filename("human", ruleset)
config.competition_mode = False
config.debug_mode = False
config.fast_mode = True
config.pathfinding_enabled = False

# Play a game
bot_a = botbowl.make_bot("search-bot")
bot_b = botbowl.make_bot("search-bot")
game = botbowl.Game(1, home, away, bot_a, bot_b, config, arena=arena, ruleset=ruleset)
print("Starting game")
game.init()
print("Game is over")
game.get_step()
