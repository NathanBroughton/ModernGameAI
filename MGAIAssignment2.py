# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 16:59:26 2022

@author: NatBr
"""
import botbowl
import numpy as np
import copy
import sys
from collections import defaultdict
from botbowl.web import server


class MyRandomBot(botbowl.Agent):

    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        self.rnd = np.random.RandomState(seed)

    def new_game(self, game, team):
        self.my_team = team

    def act(self, game):
        # Select a random action type
        while True:
            #print(game.state)
            action_choice = self.rnd.choice(game.state.available_actions)
            #print(action_choice)
            # Ignore PLACE_PLAYER actions
            if action_choice.action_type != botbowl.ActionType.PLACE_PLAYER:
                break

        # Select a random position and/or player
        position = self.rnd.choice(action_choice.positions) if len(action_choice.positions) > 0 else None
        player = self.rnd.choice(action_choice.players) if len(action_choice.players) > 0 else None

        # Make action object
        #print(action_choice.action_type)
        action = botbowl.Action(action_choice.action_type, position=position, player=player)
        #print(action)
        # Return action to the framework
        return action

    def end_game(self, game):
        pass
    
setup_actions = []
    
class MCTSBot(botbowl.Agent):
    
    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        #self.depth = 5
        self.coin = "heads"
        self.KR = "kick"
        self.rnd = np.random.RandomState(seed)
        self.formation = False
        self.m = 1
        self.off_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "x", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["x", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "x", "-", "-", "-"],
            ["x", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "x", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"]
        ]
        self.def_formation = [
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "x", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["x", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "x", "-", "-", "-", "-"],
            ["x", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "x", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"]
        ]
        self.off_formation = botbowl.Formation("Wedge offense", self.off_formation)
        self.def_formation = botbowl.Formation("Zone defense", self.def_formation)
        #self.setup_actions = []        
        
    def new_game(self,game,team):
        self.my_team = team
        
    def act(self,game):
        #while True:
        #    action_choice = self.rnd.choice(game.state.available_actions)
            
            #print(action_choice.action_type)
            #if action_choice.action_type != botbowl.ActionType.PLACE_PLAYER:
            #    break
        #print(game.state.available_actions[0])  
        print(game.state.available_actions)
        
        ##Scripted coin flip
        if(game.state.available_actions[0].action_type == botbowl.ActionType.HEADS):
            if(self.coin == "heads"):
                action = botbowl.Action(game.state.available_actions[0].action_type)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type)
        ##Scripted kick/recieve
        elif(game.state.available_actions[0].action_type == botbowl.ActionType.KICK):
            if(self.KR == "kick"):
                action = botbowl.Action(game.state.available_actions[0].action_type)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type)
        ##Scripted Formation, does not work yet!!!!
        #print(self.formation)
        #if(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_PLAYER and self.formation == False):
        #    action = botbowl.Action(game.state.available_actions[0].action_type)
        elif(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_PLAYER):
            while True:
                #print(game.state)
                action_choice = self.rnd.choice(game.state.available_actions)
                #print(action_choice)
                # Ignore PLACE_PLAYER actions
                if action_choice.action_type != botbowl.ActionType.PLACE_PLAYER:
                    break

            # Select a random position and/or player
            position = self.rnd.choice(action_choice.positions) if len(action_choice.positions) > 0 else None
            player = self.rnd.choice(action_choice.players) if len(action_choice.players) > 0 else None

            # Make action object
            #print(action_choice.action_type)
            action = botbowl.Action(action_choice.action_type, position=position, player=player)
            #print(action)
            #print(game.state.available_actions[0].positions)
            #action = setup_action.pop(0)
            #action = self.setup(game)
            #print(action)
        elif(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_BALL):
            position = self.rnd.choice(game.state.available_actions[0].positions)
            action = botbowl.Action(game.state.available_actions[0].action_type, position=position)
        #print("im here")
        ##Stuur deepcopy naar MCTS class om beste actie te kiezen
        else:
            MCTS_game = copy.deepcopy(game)
            root = MCTS(MCTS_game,self.my_team)
            action = root.BestAction()       
            
        return action
    
    def setup(self, game):
        self.my_team = game.get_team_by_id(self.my_team.team_id)
        self.opp_team = game.get_opp_team(self.my_team)
        if self.setup_actions:
            action = self.setup_actions.pop(0)
            #print(action)
            return action
        else:
            if game.get_receiving_team() == self.my_team:
                self.setup_actions = self.off_formation.actions(game,self.my_team)
                self.setup_actions.append(botbowl.Action(botbowl.ActionType.END_SETUP))
                action = self.setup_actions.pop(0)
                return action
                
            else:
                #print(self.def_formation.actions(game,self.my_team))
                self.setup_actions = self.def_formation.actions(game,self.my_team)
                self.setup_actions.append(botbowl.Action(botbowl.ActionType.END_SETUP))
                action = self.setup_actions.pop(0)
                return action
        
        
            
    def end_game(self,game):
        pass
    
class MCTS(botbowl.Agent): ##Neemt nu een deepcopy als input. Nog geen deepcopy voor child node verwerkt aangezien ik het nog niet kon testen.
                           ##Het scripted gedeelte moet nog eerst gedaan worden. Eerst volgende stap is formation 
    def __init__(self,game_copy,my_team, parent=None,parent_action=None, seed=None):
        self.depth = 5
        self.game_copy = game_copy
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self.n_visited_nodes = 0
        self.results = 0
        self.rnd = np.random.RandomState(seed)
        #self.actions = None
        self.actions = self.getActions()
        self.my_team = my_team
    
    """def UnusedActions(self,game_copy):
        #print(game.state.available_actions)
        self.actions = game_copy.getActions()
        return self.actions"""
    
    def Rewards(self): #Som rewards
        reward =self.results
        return reward
    
    def N(self):
        return self.n_visited_nodes
    
    def Expand(self):
        action = self.getActions().pop()
        self.move(action)
        next_state = copy.deepcopy(self.game_copy)
        child_node = MCTS(next_state,self.my_team, parent=self, parent_action=action)
        self.children.append(child_node)
        return child_node
    
    def TerminalNode(self):
        return self.game_copy.state.GameOver()
    
    def Rollout(self):
        current_rollout_state = self.game_copy
        #print(current_rollout_state.state.game_over)
        while(self.depth != 0 or current_rollout_state.state.game_over):
            
            moves = current_rollout_state.state.available_actions
            
            action = self.rollout_policy(moves)
            #print(action)
            self.move(action)
            self.depth -= 1
            #print(current_rollout_state.state.game_over)
        return self.game_result()
    
    def Backpropagate(self, result):
        self.n_visited_nodes += 1
        self.results += result
        if self.parent:
            #print(self.parent)
            self.parent.Backpropagate(result)
            
    def FullExpansion(self):
        return len(self.actions) == 0
    
    def BestChild(self, c_param=0.1): #Verander q naar rewards
        choices = [(c.Rewards()/c.N())+c_param * np.sqrt((2*np.log(self.N())/c.N())) for c in self.children]
        return self.children[np.argmax(choices)]
    
    def rollout_policy(self,moves):
        print(moves)
        return moves[np.random.randint(len(moves))] #Checken of dit klopt
    
    def Tree_Policy(self,d):
        current_node = self
        #print(current_node)
        while not current_node.GameOver():
            
            #if(d != 0):
            #    d -= 1
            #    print(current_node.Expand())
            if not current_node.FullExpansion():
                return current_node.Expand()
            else:
                current_node = current_node.BestChild()
        return current_node
    
    def BestAction(self):
        n_simulations = 100
        for i in range(n_simulations):
            print(i)
            v = self.Tree_Policy(self.depth)
            print(v)
            reward = v.Rollout()
            v.Backpropagate(reward)
        print(self.BestChild(c_param=0.))
        return self.BestChild(c_param=0.)
    
    def getActions(self): #Aanpassen voor position and player
        #print(self.game_copy)
        possible_actions = self.game_copy.state.available_actions
        #print(possible_actions)
        return possible_actions
    
    def GameOver(self):
        #print(self.state)
        GO = self.game_copy.state.game_over
        return GO
    
    def game_result(self): ##Hoe gaan we score implementeren
        score = (self.game_copy.state.home_team.state.score - self.game_copy.state.away_team.state.score)*20 #Assume MCTS bot is home team.
        """for player in self.game_copy.state.my_team.players:
            if(self.game_copy.state.has_ball(player) == True):
                score += 15
            if(player.game_copy.state.dead == True):
                score -= 10"""
        print("Score is:",score)
        return score
    
    def move(self,action): ##Hoe gaan we position and player kiezen 
        #print(action)
        position = self.rnd.choice(action.positions) if len(action.positions) > 0 else None #Aanpassen dit moet niet random
        player = self.rnd.choice(action.players) if len(action.players) > 0 else None
        
        action = botbowl.Action(action.action_type, position=position, player=player)
        
        return
            
# Register the bot to the framework
botbowl.register_bot('my-random-bot', MyRandomBot)
botbowl.register_bot('MCTS-bot', MCTSBot)
#server.start_server(debug=True, use_reloader=False)

if __name__ == "__main__":
    #test = MCTS(5) #We sturen game.state in MCTS niet 5
    # Load configurations, rules, arena and teams
    config = botbowl.load_config("web")
    ruleset = botbowl.load_rule_set(config.ruleset)
    arena = botbowl.load_arena(config.arena)
    home = botbowl.load_team_by_filename("human", ruleset)
    away = botbowl.load_team_by_filename("human", ruleset)
    config.competition_mode = False
    config.debug_mode = False

    # Play 10 games
    game_times = []
    for i in range(10):
        away_agent = botbowl.make_bot("my-random-bot")
        home_agent = botbowl.make_bot("MCTS-bot")

        game = botbowl.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True
        
            
        

        print("Starting game", (i+1))
        game.init()
        print("Game is over")
