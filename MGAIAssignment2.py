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
            print(game.state)
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
        print(action)
        # Return action to the framework
        return action

    def end_game(self, game):
        pass
    
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
                action = botbowl.Action(game.state.available_actions[0].action_type,position=None,player=None)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type,position=None,player=None)
        ##Scripted kick/recieve
        if(game.state.available_actions[0].action_type == botbowl.ActionType.KICK):
            if(self.KR == "kick"):
                action = botbowl.Action(game.state.available_actions[0].action_type,position=None,player=None)
            else:
                action = botbowl.Action(game.state.available_actions[1].action_type,position=None,player=None)
        ##Scripted Formation, does not work yet!!!!
        if(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_PLAYER and self.m != 5):
            position = self.rnd.choice(game.state.available_actions[0].positions) if len(game.state.available_actions[0].positions) > 0 else None
            player = self.rnd.choice(game.state.available_actions[0].players) if len(game.state.available_actions[0].players) > 0 else None
            action = botbowl.Action(game.state.available_actions[0].action_type,position=position,player=player)
            print(self.m)
            self.m += 1
        if(game.state.available_actions[0].action_type == botbowl.ActionType.PLACE_PLAYER and self.m == 5):
            print(self.m)
            action = botbowl.Action(game.state.available_actions[1].action_type,position=None,player=None)
            print(action)
        
        ##Stuur deepcopy naar MCTS class om beste actie te kiezen
        #MCTS_game = copy.deepcopy(game)
        #root = MCTS(MCTS_game,self.my_team)
        #action = root.BestAction()       
        
        ##Voer Actie uit
        
        #action_choice = self.rnd.choice(game.state.available_actions)
        #print(action_choice)
        #
        #print(action)
        
            
            #print(action_choice)
            # Ignore PLACE_PLAYER actions
            #if action_choice.action_type != botbowl.ActionType.PLACE_PLAYER:
            #    break
        
            #print(MCTS_game)

            ##Stuur deepcopy naar MCTS class om beste actie te kiezen
            #action = MCTS(MCTS_game,self.my_team)
            #best_action = action.best_action()
            #print(best_action)
            
        return action
    
    """def UnusedActions(self,game_copy):
        #print(game.state.available_actions)
        self.actions = self.game_copy.state.getActions()
        return self.actions
    
    def GameOver(self,game_copy):
        #print(game_copy.state.available_actions)
        GO = game_copy.state.game_over
        return GO
    
    def Expand(self,game_copy):
        action = self.getActions(game_copy).pop()
        next_state = self.move(game_copy,action)
        child_node = MCTS(next_state, parent=self, parent_action=action)
        self.children.append(child_node)
        return
    
    def Tree_Policy(self,game_copy,d):
        current_node = self
        while not current_node.GameOver(game_copy):
            
            if(d != 0):
                d -= 1
                return current_node.Expand(game_copy)
            else:
                current_node = current_node.BestChild()
        return current_node
    
    def BestAction(self,game_copy):
        n_simulations = 100
        for i in range(n_simulations):
            v = self.Tree_Policy(game_copy,self.depth)
            reward = v.Rollout()
            v.Backpropagate(reward)
        print(self.BestChild(c_param=0.))
        return self.BestChild(c_param=0.)
    
    def getActions(self,game_copy): #Aanpassen voor position and player
        possible_actions = game_copy.state.available_actions
        #print(possible_actions)
        return possible_actions
    
    def move(self,game_copy,action): ##Hoe gaan we position and player kiezen 
        #print(action)
        position = self.rnd.choice(action.positions) if len(action.positions) > 0 else None #Aanpassen dit moet niet random
        player = self.rnd.choice(action.players) if len(action.players) > 0 else None
        
        action = botbowl.Action(action.action_type, position=position, player=player)
        
        return"""
        
        
            
    def end_game(self,game):
        pass
    
class MCTS(botbowl.Agent): ##Neemt nu een deepcopy als input. Nog geen deepcopy voor child node verwerkt aangezien ik het nog niet kon testen.
                           ##Het scripted gedeelte moet nog eerst gedaan worden. Eerst volgende stap is formation 
    def __init__(self,game_copy,my_team, parent=None,parent_action=None):
        self.depth = 5
        self.game_copy = game_copy
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self.n_visited_nodes = 0
        self.results = 0
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
        next_state = self.move(action)
        child_node = MCTS(next_state,self.my_team, parent=self, parent_action=action)
        self.children.append(child_node)
        return
    
    def TerminalNode(self):
        return self.game_copy.state.GameOver()
    
    def Rollout(self):
        current_rollout_state = self.state
        
        while not current_rollout_state.GameOver():
            
            moves = current_rollout_state.getActions()
            
            action = self.rollout_policy(moves)
            current_rollout_state = current_rollout_state.move(action)
        return current_rollout_state.game_result()
    
    def Backpropagate(self, result):
        self.n_visited_nodes += 1
        self.results += result
        if self.parent:
            self.parent.backpropagate(result)
            
    def FullExpansion(self):
        return len(self.actions) == 0
    
    def BestChild(self, c_param=0.1): #Verander q naar rewards
        choices = [(c.Rewards()/c.N())+c_param * np.sqrt((2*np.log(self.N())/c.N())) for c in self.children]
        return self.children[np.argmax(choices)]
    
    def rollout_policy(self,moves):
        return moves[np.random.randint(len(moves))] #Checken of dit klopt
    
    def Tree_Policy(self,d):
        current_node = self
        while not current_node.GameOver():
            
            if(d != 0):
                d -= 1
                return current_node.Expand()
            else:
                current_node = current_node.BestChild()
        return current_node
    
    def BestAction(self):
        n_simulations = 100
        for i in range(n_simulations):
            v = self.Tree_Policy(self.depth)
            reward = v.Rollout()
            v.Backpropagate(reward)
        print(self.BestChild(c_param=0.))
        return self.BestChild(c_param=0.)
    
    def getActions(self): #Aanpassen voor position and player
        #print(self.state)
        possible_actions = self.game_copy.state.available_actions
        print(possible_actions)
        return possible_actions
    
    def GameOver(self):
        #print(self.state)
        GO = self.game_copy.state.game_over
        return GO
    
    def game_result(self): ##Hoe gaan we score implementeren
        score = (self.state.home_team.state.score - self.state.away_team.state.score)*20 #Assume MCTS bot is home team.
        for player in self.state.my_team.players:
            if(self.state.has_ball(player) == True):
                score += 15
            if(player.state.dead == True):
                score -= 10
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
        away_agent = botbowl.make_bot("MCTS-bot")
        home_agent = botbowl.make_bot("MCTS-bot")

        game = botbowl.Game(i, home, away, home_agent, away_agent, config, arena=arena, ruleset=ruleset)
        game.config.fast_mode = True
        
            
        

        print("Starting game", (i+1))
        game.init()
        print("Game is over")
