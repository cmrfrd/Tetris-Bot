#!/usr/bin/env python2
# Control keys:
#       Down - Drop piece faster
# Left/Right - Move piece
#         Up - Rotate piece clockwise
#     Escape - Quit game
#          P - Pause game
#     Return - Instant drfrom random import randrange as rand
import pygame, sys
from threading import Event
from tetris_player import player_process
from random import randrange as rand
import datetime
import csv
import os

# The configuration
cell_size =	18
cols =		10
rows =		22
maxfps = 	30

colors = [
(0,   0,   0  ),
(255, 85,  85),
(100, 200, 115),
(120, 108, 245),
(255, 140, 50 ),
(50,  120, 52 ),
(146, 202, 73 ),
(150, 161, 218 ),
(0,  0,  0)
]

# Define the shapes of the single parts
tetris_shapes = [
	[[1, 1, 1],
	 [0, 1, 0]],
	
	[[0, 2, 2],
	 [2, 2, 0]],
	
	[[3, 3, 0],
	 [0, 3, 3]],
	
	[[4, 0, 0],
	 [4, 4, 4]],
	
	[[0, 0, 5],
	 [5, 5, 5]],
	
	[[6, 6, 6, 6]],
	
	[[7, 7],
	 [7, 7]]
]

def rotate_clockwise(shape):
	return [ [ shape[y][x]
			for y in xrange(len(shape)) ]
		for x in xrange(len(shape[0]) - 1, -1, -1) ]

def check_collision(board, shape, offset):
	off_x, off_y = offset
	for cy, row in enumerate(shape):
		for cx, cell in enumerate(row):
			try:
				if cell and board[ cy + off_y ][ cx + off_x ]:
					return True
			except IndexError:
				return True
	return False

def remove_row(board, row):
	del board[row]
	return [[0 for i in xrange(cols)]] + board
	
def join_matrixes(mat1, mat2, mat2_off):
	off_x, off_y = mat2_off
	for cy, row in enumerate(mat2):
		for cx, val in enumerate(row):
			mat1[cy+off_y-1	][cx+off_x] += val
	return mat1

def new_board():
	board = [ [ 0 for x in xrange(cols) ]
			for y in xrange(rows) ]
	board += [[ 1 for x in xrange(cols)]]
	return board

class TetrisApp(object):
	def __init__(self, start_auto=False, screen=True, record=False):
		pygame.init()
		pygame.key.set_repeat(250,25)

		self.width = cell_size*(cols+6)
		self.height = cell_size*rows
		self.rlim = cell_size*cols
		self.bground_grid = [[ 8 if x%2==y%2 else 0 for x in xrange(cols)] for y in xrange(rows)]
		
		self.default_font =  pygame.font.Font(
			pygame.font.get_default_font(), 12)
		
		if screen:
			self.screen = pygame.display.set_mode((self.width, self.height))
		else:
			self.screen = None

		self.record = record
		self.record_list = []

		pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
		                                             # mouse movement
		                                             # events, so we
		                                             # block them.
		self.next_piece = tetris_shapes[rand(len(tetris_shapes))]
		self.init_game()

		self.auto = Event()
		self.player = player_process(self)
		self.player.start()
		self.pieces_processed = 0
		print "starting process"

		if start_auto:self.flip()		
	
	def new_piece(self):
		self.piece = self.next_piece[:]
		self.next_piece = tetris_shapes[rand(len(tetris_shapes))]
		#self.next_piece = tetris_shapes[5]
		self.piece_x = int(cols / 2 - len(self.piece[0])/2)
		self.piece_y = 0
		
		if check_collision(self.board,
		                   self.piece,
		                   (self.piece_x, self.piece_y)):
			self.gameover = True
	
	def init_game(self):
		self.board = new_board()
		self.new_piece()
		self.level = 1
		self.score = 0
		self.lines = 0
		pygame.time.set_timer(pygame.USEREVENT+1, 1000)
	
	def disp_msg(self, msg, topleft):
		x,y = topleft
		for line in msg.splitlines():
			self.screen.blit(
				self.default_font.render(
					line,
					False,
					(255,255,255),
					(0,0,0)),
				(x,y))
			y+=14
	
	def center_msg(self, msg):
		for i, line in enumerate(msg.splitlines()):
			msg_image =  self.default_font.render(line, False,
				(255,255,255), (0,0,0))
		
			msgim_center_x, msgim_center_y = msg_image.get_size()
			msgim_center_x //= 2
			msgim_center_y //= 2
		
			self.screen.blit(msg_image, (
			  self.width // 2-msgim_center_x,
			  self.height // 2-msgim_center_y+i*22))
	
	def draw_matrix(self, matrix, offset):
		off_x, off_y  = offset
		for y, row in enumerate(matrix):
			for x, val in enumerate(row):
				if val:
					pygame.draw.rect(
						self.screen,
						colors[val],
						pygame.Rect(
							(off_x+x) *
							  cell_size,
							(off_y+y) *
							  cell_size, 
							cell_size,
							cell_size),0)
	
	def add_cl_lines(self, n):
		linescores = [0, 40, 100, 300, 1200]
		self.lines += n
		self.score += linescores[n] * self.level
		if self.lines >= self.level*6:
			self.level += 1
			newdelay = 1000-50*(self.level-1)
			newdelay = 100 if newdelay < 100 else newdelay
			pygame.time.set_timer(pygame.USEREVENT+1, newdelay)
	
	def move(self, delta_x):
		if not self.gameover and not self.paused:
			new_x = self.piece_x + delta_x
			if new_x < 0:
				new_x = 0
			if new_x > cols - len(self.piece[0]):
				new_x = cols - len(self.piece[0])
			if not check_collision(self.board,
			                       self.piece,
			                       (new_x, self.piece_y)):
				self.piece_x = new_x

	def quit(self):
		print "shutting down process"
		self.player.shutdown()
		self.auto.set()
		if self.screen:
			self.center_msg("Exiting...")		
			pygame.display.update()
		if self.record:
			filepath = "gameplays/" + str(datetime.datetime.today().toordinal()) + "-" + str(self.pieces_processed) + ".csv"
			with open(filepath, "wb") as record_file:
				csv_file_writer = csv.writer(record_file, delimiter=" ")
				for play in self.record_list:
					csv_file_writer.writerow(play)
		print "ending game"
		print "%d" % (self.pieces_processed)
		sys.exit()
	
	def drop(self, manual):
		if not self.gameover and not self.paused:
			self.score += 1 if manual else 0
			self.piece_y += 1
			if check_collision(self.board,
			                   self.piece,
			                   (self.piece_x, self.piece_y)):
				self.board = join_matrixes(
				  self.board,
				  self.piece,
				  (self.piece_x, self.piece_y))
				if self.record:self.record_list.append((self.piece_x, self.piece))
				self.new_piece()
				cleared_rows = 0
				while True:
					for i, row in enumerate(self.board[:-1]):
						if 0 not in row:
							self.board = remove_row(
							  self.board, i)
							cleared_rows += 1
							break
					else:
						break
				self.add_cl_lines(cleared_rows)
				self.pieces_processed +=1
				return True
		return False
	
	def insta_drop(self):
		if not self.gameover and not self.paused:
			while(not self.drop(True)):
				pass
	
	def rotate_piece(self):
		if not self.gameover and not self.paused:
			new_piece = rotate_clockwise(self.piece)
			if not check_collision(self.board,
			                       new_piece,
			                       (self.piece_x, self.piece_y)):
				self.piece = new_piece
	
	def toggle_pause(self):
		self.paused = not self.paused
	
	def start_game(self):
		if self.gameover:
			self.init_game()
			self.gameover = False

	def flip(self):
		self.auto.clear() if self.auto.is_set() else self.auto.set()
	
	def run(self):
		key_actions = {
			'ESCAPE':	self.quit,
			'LEFT':		lambda:self.move(-1),
			'RIGHT':	lambda:self.move(+1),
			'DOWN':		lambda:self.drop(True),
			'UP':		self.rotate_piece,
			'p':		self.toggle_pause,
			's':	        self.start_game,
			'SPACE':	self.insta_drop,
			'LSHIFT':	self.flip
		}
		
		self.gameover = False
		self.paused = False
		
		dont_burn_my_cpu = pygame.time.Clock()

		if self.screen:
			while 1:
				self.screen.fill((0,0,0))
				if self.gameover:
					self.center_msg("""Game Over!\nYour score: %d
Press space to continue""" % self.score)
					#self.quit()
					return self.pieces_processed
				else:
					if self.paused:
						self.center_msg("Paused")
					else:
						pygame.draw.line(self.screen,
							(255,255,255),
							(self.rlim+1, 0),
							(self.rlim+1, self.height-1))
						self.disp_msg("Next:", (
							self.rlim+cell_size,
							2))
						self.disp_msg("Score: %d\n\nLevel: %d\
							\nLines: %d" % (self.score, self.level, self.lines),
							(self.rlim+cell_size, cell_size*5))
						self.disp_msg("'Left Shift'\nfor Auto Play", (self.rlim + cell_size, cell_size * 10))

						self.draw_matrix(self.bground_grid, (0,0))
						self.draw_matrix(self.board, (0,0))
						self.draw_matrix(self.piece,
							(self.piece_x, self.piece_y))
						self.draw_matrix(self.next_piece,
							(cols+1,2))
				pygame.display.update()
			
				if not self.auto.is_set():
					for event in pygame.event.get():
						if event.type == pygame.USEREVENT+1:
							self.drop(False)
						elif event.type == pygame.QUIT:
							self.quit()
						elif event.type == pygame.KEYDOWN:
							for key in key_actions:
								if event.key == eval("pygame.K_"
								+key):
									key_actions[key]()
				else:
					for event in pygame.event.get():
						if event.type == pygame.USEREVENT+1:
							self.drop(False)
						elif event.type == pygame.QUIT:
							self.quit()
						elif event.type == pygame.KEYDOWN:
							for key in key_actions:
								if event.key == eval("pygame.K_"
								+key) and (key == "LSHIFT" or key == "p" or key == "ESCAPE"):
									key_actions[key]()
								
				dont_burn_my_cpu.tick(maxfps)

		elif not self.screen:
			self.auto.set()
			while 1:
				if self.gameover:
					#self.quit()					
					return self.pieces_processed			
				for event in pygame.event.get():
					if event.type == pygame.USEREVENT+1:
						self.drop(False)
					elif event.type == pygame.QUIT:
						self.quit()
					elif event.type == pygame.KEYDOWN:
						for key in key_actions:
							if event.key == eval("pygame.K_"
							+key) and (key == "ESCAPE"):
								key_actions[key]()
				dont_burn_my_cpu.tick(maxfps)


if __name__ == '__main__':
	print "1 = Yes"
	print "0 = No"
	if len(sys.argv) <= 3:
		auto = bool(int(raw_input("Auto Mode: ")))
		isscreen = bool(int(raw_input("Screen Visible: ")))
		record = bool(int(raw_input("Record Gameplay: ")))
	else:
		auto = bool(int(sys.argv[1]))
		isscreen = bool(int(sys.argv[2]))
		record = bool(int(sys.argv[3]))

	App = TetrisApp(start_auto=auto, screen=isscreen, record=record)
	App.run()
	App.quit()
