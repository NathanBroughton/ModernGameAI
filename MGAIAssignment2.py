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

        # Return action to the framework
        return action

    def end_game(self, game):
        pass
    
class MCTSBot(botbowl.Agent):
    
    def __init__(self, name, seed=None):
        super().__init__(name)
        self.my_team = None
        
    def new_game(self,game,team):
        self.my_team = team
        
    def act(self,game):
        
        #print(sys.getsizeof(game))
        print(game)
        #print(MCTS_game)
        while True:
            MCTS_game = copy.deepcopy(game)
            ##Stuur deepcopy naar MCTS class om beste actie te kiezen
            ##Voer Actie uit
            
    def end_game(self,game):
        pass
    
class MCTS(botbowl.Agent): ##Kan nu alleen alles per state herkennen maar dit moet het volgende doen:
    ## Een state is nu een deepcopy van de orginele game
    ## Elke keer als we MCTS opnieuw aanroepen moet er een nieuwe deepcopy gemaakt worden voor de childstate
    def __init__(self,state,my_team, parent=None,parent_action=None):
        self.depth = 5
        self.state = state
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self.n_visited_nodes = 0
        self.results = 0
        #self.actions = None
        self.actions = self.UnusedActions()
        self.my_team = my_team
    
    def UnusedActions(self):
        #print(game.state.available_actions)
        self.actions = self.state.getActions()
        return self.actions
    
    def Rewards(self): #Som rewards
        reward =self.results
        return reward
    
    def N(self):
        return self.n_visited_nodes
    
    def Expand(self):
        action = self.UnusedActions()
        next_state = self.state.move(action)
        child_node = MCTS(next_state, parent=self, parent_action=action)
        self.children.append(child_node)
        return
    
    def TerminalNode(self):
        return self.state.GameOver()
    
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
        choices = [(c.Rewards()/c.n())+c_param * np.sqrt((2*np.log(self.n())/c.n())) for c in self.children]
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
        possible_actions = self.state.available_actions
        return possible_actions
    
    def GameOver(self):
        GO = self.state.game_over
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
