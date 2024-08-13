import heapq
import random
import pygame

# Constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
NUM_WALLS = 200  # Max number of walls to try
MIN_WALLS = NUM_WALLS   # Minimum number of walls to start with
WALL_INCREMENT = 10  # Number of walls to add in each step
FREE_RADIUS = 5  # Radius around start and end nodes to keep free of walls

# Directions for movement
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up

# Node class for A* algorithm
class Node:
    def __init__(self, pos):
        self.pos = pos
        self.g = float('inf')  # Cost from start to this node
        self.h = 0  # Heuristic cost from this node to end
        self.f = float('inf')  # Total cost (g + h)
        self.parent = None
        self.walkable = True

    def __lt__(self, other):
        return self.f < other.f

def draw_nodes(nodes):
    for node in nodes:
        color = WHITE
        if not node.walkable:
            color = BLACK
        elif node == start:
            color = GREEN
        elif node == end:
            color = RED
        elif node in path:
            color = BLUE
        pygame.draw.rect(win, color, (node.pos[0] * CELL_SIZE, node.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(win, BLACK, (node.pos[0] * CELL_SIZE, node.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

def get_node_at_pos(x, y):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        return next((n for n in nodes if n.pos == (x // CELL_SIZE, y // CELL_SIZE)), None)
    return None

def get_neighbors(node, nodes):
    neighbors = []
    for d in DIRECTIONS:
        pos = (node.pos[0] + d[0], node.pos[1] + d[1])
        if 0 <= pos[0] < WIDTH // CELL_SIZE and 0 <= pos[1] < HEIGHT // CELL_SIZE:
            neighbor = next((n for n in nodes if n.pos == pos), None)
            if neighbor and neighbor.walkable:
                neighbors.append(neighbor)
    return neighbors

def a_star(nodes, start, end):
    open_set = []
    heapq.heappush(open_set, start)
    start.g = 0
    start.f = start.h

    closed_set = set()
    while open_set:
        current = heapq.heappop(open_set)
        if current == end:
            reconstruct_path(end)
            return True

        closed_set.add(current)

        for neighbor in get_neighbors(current, nodes):
            if neighbor in closed_set:
                continue

            tentative_g = current.g + 1
            if tentative_g < neighbor.g:
                neighbor.parent = current
                neighbor.g = tentative_g
                neighbor.h = abs(neighbor.pos[0] - end.pos[0]) + abs(neighbor.pos[1] - end.pos[1])
                neighbor.f = neighbor.g + neighbor.h
                if neighbor not in open_set:
                    heapq.heappush(open_set, neighbor)

    return False

def reconstruct_path(node):
    global path
    path = []
    while node:
        path.append(node)
        node = node.parent
    path.reverse()  # To show path from start to end

def reset_nodes(nodes):
    for node in nodes:
        node.g = float('inf')
        node.h = 0
        node.f = float('inf')
        node.parent = None
        node.walkable = True  # Ensure nodes are walkable when resetting

def place_random_walls(nodes, num_walls, free_radius, start, end):
    # Get all walkable nodes (excluding start and end nodes) within free radius
    walkable_nodes = [node for node in nodes if node.walkable and node != start and node != end and not is_within_free_radius(node.pos, start.pos, end.pos, free_radius)]
    
    # Randomly select nodes to be walls
    walls_to_place = random.sample(walkable_nodes, min(num_walls, len(walkable_nodes)))
    
    for node in walls_to_place:
        node.walkable = False

def is_within_free_radius(node_pos, start_pos, end_pos, radius):
    def within_radius(p1, p2, radius):
        return abs(p1[0] - p2[0]) <= radius and abs(p1[1] - p2[1]) <= radius
    
    return within_radius(node_pos, start_pos, radius) or within_radius(node_pos, end_pos, radius)

def regenerate_labyrinth(nodes, min_walls, free_radius):
    global path
    path = []
    reset_nodes(nodes)  # Clear existing walls and reset node states
    place_random_walls(nodes, min_walls, free_radius, start, end)
    while not a_star(nodes, start, end):
        reset_nodes(nodes)  # Clear existing walls
        place_random_walls(nodes, min_walls, free_radius, start, end)
    #print("Path found!")

# Initialize Pygame
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("A* Pathfinding")

# Create nodes
nodes = [Node((x, y)) for x in range(WIDTH // CELL_SIZE) for y in range(HEIGHT // CELL_SIZE)]

# Set start and end nodes
start = next(n for n in nodes if n.pos == (0, 0))
end = next(n for n in nodes if n.pos == (WIDTH // CELL_SIZE - 1, HEIGHT // CELL_SIZE - 1))
path = []

# Main loop
active = False
running = True
while running:
    win.fill(WHITE)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                active = not active
            elif event.key == pygame.K_q:
                running = False

    if active:
        regenerate_labyrinth(nodes, MIN_WALLS, FREE_RADIUS)

    draw_nodes(nodes)
    pygame.display.flip()
    pygame.time.delay(50)

pygame.quit()
