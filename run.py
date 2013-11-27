import agent, evaluation, game, random

def run_game(g, agents):
	# Welcome message
	print "\nWelcome to the card game BS! You are player 0, " + \
			  "and there are {} other players.".format(len(g.players)-1)
	print "==============================================================================="
	print "===============================================================================\n"
	
	# Run game
	over = False
	currPlayer = 0
	while not over:
		# Print turn information
		g.printTurn()

		# Get actions for current player and select one to take
		currAgent = agents[currPlayer]
		moves = g.getActions(currPlayer)
		action = currAgent.getAction(moves, g)
		g.takeAction(action, currPlayer, verbose=True)
		currPlayer = g.currPlayer

		# Check if anyone wants to call BS. If so, randomly select one to do so.
		callers = []
		for i in range(len(agents)):
			if agents[i].getCall(g):
				callers.append(i)
		if callers:
			caller = random.choice(callers)
			g.takeCall(caller, verbose=True)

		over = g.isOver()
		print "\n=========================" + \
		      "======================================================\n"

	winner = g.winner()
	print "The winner is player {}!".format(winner)

NUM_DECKS = 1
NUM_COMPUTERS = 1

def main(args=None):
	arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	for i in range(1, NUM_COMPUTERS+1):
		arr.append(agent.HonestAgent(i))
	g = game.Game(len(arr), NUM_DECKS)
	run_game(g, arr)

if __name__=="__main__":
    main()