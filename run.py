import agent, copy, evaluation, game, math, random, itertools

NUM_DECKS = 1
NUM_CARDS = 5 #Must be <= 13 and non-zero

def run_game(g, agents, verbose=1):
	# Welcome message
	if verbose != 0:
		print "\nWelcome to the card game BS! You are player 0, " + \
				  "and there are {} other players.".format(len(g.players)-1)
		print "==============================================================================="
		print "===============================================================================\n"
	
	# Run game
	over = False
	currPlayer = 0
	totalAgentCalls = 0.0
	totalPossibleCalls = 0.0
	while not over:
		# Print turn information
		if verbose != 0:
			g.printTurn()

		# Get actions for current player and select one to take
		currAgent = agents[currPlayer]
		moves = g.getActions(currPlayer)
		action = currAgent.getAction(moves, g)
		g.takeAction(action, currPlayer, verbose)
		currPlayer = g.currPlayer

		currCaller = g.currPlayer
		while(True):
			# Take the first call after the player who just played
			call = agents[currCaller].getCall(g, verbose)
			if call:
				if currCaller == 0:        #Debug
					totalAgentCalls += 1   #Debug
				g.takeCall(currCaller, verbose)
				break
			currCaller = (currCaller + 1) % g.numPlayers

			# If we wrap around to the player who just played, break
			if currCaller == (g.currPlayer - 1) % g.numPlayers:
				break
		
		totalPossibleCalls += 1            #Debug

		over = g.isOver()
		if verbose != 0:
			print "\n=========================" + \
			      "======================================================\n"
	#print "Frequency of agent calls: ", totalAgentCalls / totalPossibleCalls #Debug
	winner = g.winner()
	#print "The winner is player {}!".format(winner)
	return winner

def extractFeatures(state):
	game, playerNum = state
	features = []

	# Num cards in own hand
	features.append(sum(game.players[playerNum].hand))

	# Num cards in opponents hands
	for i in range(len(game.players)):
		if i != playerNum:
			features.append(sum(game.players[i].hand))
	
	# Size of discard pile
	features.append(sum(game.discard))

	# Number of i of a kind you have in your hand
	for i in range(0, 5):
		features.append(game.players[playerNum].hand.count(i))

	# Number of next two required cards you have
	
	# print "Current player: ", game.currPlayer
	# print "playerNum: ", playerNum
	# print "Current Card: ", game.currCard
	if game.currPlayer == playerNum:
		nextCard = (game.currCard + game.numPlayers) % NUM_CARDS
	else:
		nextCard = (game.currCard + (playerNum - game.currPlayer) % game.numPlayers) % NUM_CARDS
	nextNextCard = (nextCard + game.numPlayers) % NUM_CARDS
	# print "Next card: ", nextCard
	# print "Next next card: ", nextNextCard
	# print "\n"
	features.append(game.players[playerNum].hand[nextCard])
	features.append(game.players[playerNum].hand[nextNextCard])

	return features

def logLinearEvaluation(state, w):
    """
    Evaluate the current state using the log-linear evaluation
    function.

    @param state : Tuple of (game, playerNum), the game is
    a game object (see game.py for details, and playerNum
    is the number of the player for whose utility the state is
    being evaluated.

    @param w : List of feature weights.

    @returns V : Evaluation of current game state.
    """
    features = extractFeatures(state)
    dotProduct = sum([features[i] * w[i] for i in range(len(features))])
    V = float(1)/(1 + math.exp(-dotProduct))
    return V

def TDUpdate(state, nextState, reward, w, eta):
    """
    Given two sequential game states, updates the weights
    with a step size of eta, using the Temporal Difference learning
    algorithm.

    @param state : Tuple of game state (game object, player).
    @param nextState : Tuple of game state (game object, player),
    note if the game is over this will be None. In this case, 
    the next value for the TD update will be 0.
    @param reward : The reward is 1 if the game is over and your
    player won, 0 otherwise.
    @param w : List of feature weights.
    @param eta : Step size for learning.

    @returns w : Updated weights.
    """
    if nextState:
        residual = reward + logLinearEvaluation(nextState, w) - logLinearEvaluation(state, w)
    else: 
        residual = reward - logLinearEvaluation(state, w)
    phi = extractFeatures(state)
    expTerm = math.exp(-sum([phi[i] * w[i] for i in range(len(phi))]))
    gradCoeff = expTerm / math.pow((1 + expTerm), 2)
    for i in range(len(w)):
        gradient = phi[i] * gradCoeff
        w[i] += (eta * residual * gradient)
    return w

def train(numAgents=3, numGames=30):
	alpha = 1e-1
	numFeats = 8 + numAgents #Debug
	w = [random.gauss(1e-3, 1e-1) for _ in range(numFeats)]
	agents = [agent.ReflexAgent(i, logLinearEvaluation, w) for i in range(numAgents)]
	# agents = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numAgents):
	# 	agents.append(agent.ReflexAgent(i, evaluation.simpleEvaluation))

	i = 0
	while i < numGames:
		#print i
		g = game.Game(len(agents), NUM_DECKS)

		# Run game
		over = False
		currPlayer = 0

		cycle = False
		turnCounter = 0
		threshold = 100
		oldW = list(w)
		oldAgents = copy.deepcopy(agents)

		while not over:
			if turnCounter > threshold:
				cycle = True
				break
			turnCounter += 1
			#print turnCounter

			states = [(g.clone(), currPlayer)]

			# Get actions for current player and select one to take
			currAgent = agents[currPlayer]
			moves = g.getActions(currPlayer)
			action = currAgent.getAction(moves, g)
			# if currPlayer == 0:
			# 		print "========================================="
			# print "Required card: ", g.currCard
			g.takeAction(action, currPlayer, verbose=0)
			# print "Hands: ", g.players[0].hand, g.players[1].hand, g.players[2].hand
			currPlayer = g.currPlayer

			currCaller = g.currPlayer
			
			# calls = []
			# for i in range(g.numPlayers):
			# 	call = agents[i].getCall(g, verbose=1)
			# 	if call:
			# 		calls.append(i)
			# 		states.append((g.clone(), i))

			# caller = random.choice(calls) if calls else None
			# if caller:
			# 	g.takeCall(caller, verbose=1)

			while(True):
				# Take the first call after the player who just played
				call = agents[currCaller].getCall(g, verbose=0)
				states.append((g.clone(), currCaller))
				if call:
					g.takeCall(currCaller, verbose=0)
					break
				currCaller = (currCaller + 1) % g.numPlayers

				# If we wrap around to the player who just played, break
				if currCaller == (g.currPlayer - 1) % g.numPlayers:
					break

			for state in states:
				nextState = (g, state[1])
				w = TDUpdate(state,nextState,0,w,alpha)

			for a in agents:
				a.setWeights(w)

			over = g.isOver()

		if not cycle:
			winner = g.winner()
			w = TDUpdate((g, winner),None, 1.0, w ,alpha)
			i += 1
			print "Noncycle"
		else:
			w = oldW
			agents = oldAgents
		#print "The winner is player {}!".format(winner)

	# save weights
	# fid = open("weights.bin",'w')
	# import pickle
	# pickle.dump(w,fid)
	# fid.close()
	print w #Debug
	return w

def test(agents, numGames=10):
	playerWin = [0 for i in range(len(agents))] #Our agent won, other agent won
	for i in range(numGames):
		#print "On game: " + str(i + 1)
		g = game.Game(len(agents), NUM_DECKS)
		winner = run_game(g, agents, verbose=0) #Debug
		playerWin[winner] += 1
	for j in range(len(agents)):
		if j == 0: #Debug
			print "Player {} win rate: {}".format(j, float(playerWin[j]) / sum(playerWin))
	

def main(args=None):
	
	# arr = [agent.HumanAgent(0)]
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, NUM_COMPUTERS+1):
	# 	arr.append(agent.RandomAgent(i))
	# g = game.Game(len(arr), NUM_DECKS)
	numPlayers = 3
	numIters = 20
	numTrials = 10

	# print "Training on {} players for {} iterations...".format(numPlayers, numIters)
	# w = train(numPlayers, numIters)

	# print "Trained agent against random agents"
	# arr = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numPlayers):
	#  	arr.append(agent.RandomAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Trained agent against simple evaluation agents"
	# arr = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numPlayers):
	#  	arr.append(agent.ReflexAgent(i, evaluation.simpleEvaluation))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Trained agent against honest agents"
	# arr = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.HonestAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Trained agent against dishonest agents"
	# arr = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.DishonestAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Trained agent against AlwaysCallBSAgent"
	# arr = [agent.ReflexAgent(0, logLinearEvaluation, w)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.AlwaysCallBSAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Simple evaluation against random agents"
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, numPlayers):
	#  	arr.append(agent.RandomAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Simple agent against simple evaluation agents"
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, numPlayers):
	#  	arr.append(agent.ReflexAgent(i, evaluation.simpleEvaluation))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Simple agent against honest agents"
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.HonestAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Simple agent against dishonest agents"
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.DishonestAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	# print "Simple agent against AlwaysCallBSAgent"
	# arr = [agent.ReflexAgent(0, evaluation.simpleEvaluation)]
	# for i in range(1, numPlayers):
	# 	arr.append(agent.AlwaysCallBSAgent(i))
	# g = game.Game(numPlayers, NUM_DECKS)
	# test(arr, numTrials)

	while True:
		g = game.Game(numPlayers, NUM_DECKS)
		run_game(g, [agent.HumanAgent(0), agent.ReflexAgent(1, evaluation.simpleEvaluation), agent.ReflexAgent(2, evaluation.simpleEvaluation)])

if __name__=="__main__":
    main()
