# -*- coding: utf-8 -*-
'''
#-------------------------------------------------------------------------------
# NATIONAL UNIVERSITY OF SINGAPORE - NUS
# SINGAPORE INSTITUTE FOR NEUROTECHNOLOGY - SINAPSE
# Singapore
# URL: http://www.sinapseinstitute.org
#-------------------------------------------------------------------------------
# Neuromorphic Engineering Group
# Author: Andrei Nakagawa-Silva, MSc
# Contact: nakagawa.andrei@gmail.com
#-------------------------------------------------------------------------------
# Description: Library for building state machines
#-------------------------------------------------------------------------------
# Implementation:
#	Inspired by: https://github.com/pytransitions/transitions
#-------------------------------------------------------------------------------
'''
#-------------------------------------------------------------------------------
#LIBRARIES
import time
from threading import Thread
#-------------------------------------------------------------------------------
#State class
class StateMachine(object):
	def __init__(self,initial_state=None,states=[],stateChangedCallback=None):
		self.transitions = {} #dictionary that stores the transitions
		self.states = states #list containing possible states
		self.state = initial_state #initial state
		#callback used for signaling that a state changed
		self.stateChanged = stateChangedCallback

	#add a new state to the list
	def add_state(self,state):
		self.states.append(state)

	#create a transition
	#trigger is the name of the action used for changing state
	#prevst is the previous state, indicates which states can change into the next
	#prevst can be an array comprising possible states or '*' if any state can change
	#into the next state
	#nextst is the next state
	#function is the method that should be called during transition
	def add_transition(self,trigger,prevst,nextst,function=None):
		self.transitions[trigger] = [prevst,nextst,function]

	#change the state
	def change(self,trigger):
		#check if the action has been registered
		if trigger in self.transitions:
			#check if it is possible to change state
			if self.state in self.transitions[trigger][0] or self.transitions[trigger][0] == '*':
				#check if the transition is made by a custom-made method
				if self.transitions[trigger][2] is not None:
					th = Thread(target=self.run, args=([self.transitions[trigger]]))
					th.daemon = True
					th.start()
				else:
					self.state = self.transitions[trigger][1]
					self.stateChanged()
			else:
				return False #can't transit from current state
		else:
			return False #trigger not registered

	#the transition method runs in a separate thread
	def run(self,transition):
		transition[2]() #calls the method
		self.state = transition[1] #after the method is finished, change the state
		self.stateChanged() #callback signaling state changed
#-------------------------------------------------------------------------------
if __name__ == '__main__':

	def work():
		time.sleep(10)

	def stateChanged():
		global machine
		print('changed!', machine.state)

	machine = StateMachine('idle',['idle','running','working','hungry'],stateChanged)
	machine.add_transition('work','idle','working')
	machine.add_transition('work more',['working','running'],'hungry',work)
	machine.change('work')
	print(machine.state)
	machine.change('work more')
	a = input()
