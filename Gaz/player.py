from time import sleep
from threading import Thread, Event
from KNN import Game_Reader, k_nearest_neighbors
from greedy import greedy
from math import e

class no_brain(object):
	def __init__(self):
		pass
	def get_next_move(self, board, piece):
		raise NotImplementedError("No brain has been provided to Gaz")

class player(Thread):
	def __init__(self, app, mode):
		Thread.__init__(self)
		self.exit = Event()
		self.app = app
		self.mode = mode

	def best_move_by_KNN(self, pieces, board, games=10, k=5):
		reader = Game_Reader(pieces, board)
		reader.read_model("10gamemodel")

		while not self.exit.is_set() and self.app.auto.wait() and not self.app.gameover:
			current_state_vector = reader.feature_dict_from_board( zip(*self.app.board) ).values()
			move = k_nearest_neighbors(k, reader.dataset, self.get_piece_index(self.app.piece[:]), current_state_vector)
			yield move

	def execute_move(self, move, time=0.01):
		'''executes move based on tuple (rotation, x_coord)
		'''
		#while self.app.piece != move[1] and not self.app.gameover:
		#	self.app.rotate_piece()

		for i in range(move[1]):self.app.rotate_piece()
			
		move_int = move[0] - self.app.piece_x
		self.app.move(move_int)
			
		self.app.insta_drop()

		sleep(time)
		return True

	def run(self):
		debug = True
		player_pieces_processed = 0

		#To implement KNN uncomment line below as well as KNN line in while loop
		player_brain = no_brain()
		if self.mode[0] == "greedy":
			player_brain = greedy(0.01)
		if self.mode[0] == "knn":
			KNN_mover = self.best_move_by_KNN(tetris_shapes, Board)

		while not self.exit.is_set() and self.app.auto.wait() and not self.app.gameover:
			#make sure player and game are in sync with pieces processed
			if self.app.pieces_processed != player_pieces_processed:
				player_pieces_processed += 1
				continue
			
			move = player_brain.get_next_move(Board(zip(*self.app.board)), self.app.piece)

			#to use KNN uncomment this line as well as instantiation of iterator before while loop
			move = KNN_mover.next()
			#print move

			if self.execute_move(move):
				player_pieces_processed += 1

		print "process has ended"

	def shutdown(self):
		print "executing shutdown"
		self.exit.set()
