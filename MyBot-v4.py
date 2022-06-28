import hlt
import logging
from collections import OrderedDict
import math
import heapq

from hlt.entity import Planet

game = hlt.Game("Jarvis-v4")
logging.info("Starting my Jarvis bot")

path_map = None


def get_cell_neighbours(x: int, y: int, width, height):
    neighbours = []

    if x == 0:
        neighbours.append((1, y))

        if y == 0:
            neighbours.append((x, 1))
        elif y == height-1:
            neighbours.append((x, y-1))
        else:
            neighbours.append((x, y-1))
            neighbours.append((x, y+1))

    elif x == width-1:
        neighbours.append((x, y))

        if y == 0:
            neighbours.append((x, 1))
        elif y == height - 1:
            neighbours.append((x, y - 1))
        else:
            neighbours.append((x, y - 1))
            neighbours.append((x, y + 1))

    else:
        neighbours.append((x-1, y))
        neighbours.append((x+1, y))

        if y == 0:
            neighbours.append((x, 1))
        elif y == height - 1:
            neighbours.append((x, y - 1))
        else:
            neighbours.append((x, y - 1))
            neighbours.append((x, y + 1))

    return neighbours


def create_costs_map(start_x, start_y, map_width, map_height):
    costs_map = [[0 for x in range(map_width)] for y in range(map_height)]

    for y in range(map_height):
        for x in range(map_width):
            distance = math.sqrt(
                math.pow(x - start_x, 2) +
                math.pow(y - start_y, 2)
            )

            costs = math.ceil(distance)

            costs_map[y][x] = costs

    return costs_map


def a_star(start_x, start_y, goal_x, goal_y):
    map_width, map_height = game.initial_map.width, game.initial_map.height
    costs_map = create_costs_map(start_x, start_y, map_width, map_height)
    start = (start_x, start_y)
    goal = (goal_x, goal_y)

    for row in costs_map:
        logging.info(row)
    logging.info("")
    logging.info("")
    logging.info("")
    logging.info("")

    frontier = []
    came_from = dict()
    cost_so_far = dict()

    # Startwert hinzuzufügen
    heapq.heappush(frontier, (0, start))
    came_from[start] = None
    cost_so_far[start] = 0

    # solange frontier nicht leer ist, wird eine Route gesucht
    while frontier:
        (priority, (current_node_x, current_node_y)) = heapq.heappop(frontier)
        current_node = (current_node_x, current_node_y)

        if current_node == goal:
            break

        for (next_node_x, next_node_y) in get_cell_neighbours(current_node_x, current_node_y, map_width, map_height):
            next_node = (next_node_x, next_node_y)

            # prüfen, ob Nachbar kein Planet ist
            if path_map[next_node_y][next_node_x] == 1:
                continue

            # Kosten für diese Zelle berechnen
            cell_costs = costs_map[next_node_y][next_node_x]
            path_costs = cost_so_far[current_node] + cell_costs

            # wenn dieser Pfad zu der Zelle der günstigste zu dieser ist
            if next_node not in cost_so_far or path_costs < cost_so_far[next_node]:
                cost_so_far[next_node] = path_costs
                priority = path_costs

                next_node_heap = (priority, next_node)

                heapq.heappush(frontier, next_node_heap)
                came_from[next_node] = current_node

    cell = goal
    path = [goal]

    while cell is not start:
        predecessor = came_from[cell]

        if predecessor is None:
            break

        path.append(predecessor)
        cell = predecessor

    path.reverse()
    logging.info(path)


def initialize_map(width: int, height: int, planets: list[Planet]):
    global path_map
    path_map = [ [ 0 for x in range(width) ] for y in range(height) ]

    for y in range(height):
        for x in range(width):
            for planet in planets:
                planet_x = int(planet.x)
                planet_y = int(planet.y)
                planet_r = float(planet.radius)

                if math.pow(x - planet_x, 2) + math.pow(y - planet_y, 2) < math.pow(planet_r, 2):
                    path_map[y][x] = 1


def fly_to(ship: hlt.entity.Ship, object: hlt.entity):
    navigate_command = ship.navigate(
                ship.closest_point_to(object),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)

    if navigate_command:
        command_queue.append(navigate_command)
        return object
    else:
        return None


while True:
    game_map = game.update_map()
    command_queue = []
    planned_planets = []
    ships_assigned_to_target_ship = {}

    if path_map is None:
        initialize_map(game_map.width, game_map.height, game_map.all_planets())
        a_star(5, 5, game_map.width-5, game_map.height-5)
    
    for ship in game_map.get_me().all_ships():
        ship: hlt.entity.Ship

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue  # Skip this ship

        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

        empty_planets_by_distance = []
        enemy_ships_by_distance = []

        own_ships = game_map.get_me().all_ships()

        for object in entities_by_distance:
            entity = entities_by_distance[object][0]
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    empty_planets_by_distance.append(entity)
            elif isinstance(entity, hlt.entity.Ship):
                if entity not in own_ships:
                    enemy_ships_by_distance.append(entity)

        if len(empty_planets_by_distance) > 0: # gibt es nicht besetzte Planeten
            target_planet = empty_planets_by_distance[0] # nächsten leeren Planeten nehmen

            # irgendeine Suche
            if target_planet in planned_planets:  # nächsten leeren Planeten nehmen, der noch nicht von eigenen Schiffen angeflogen wird (nötig, da Schiff sonst kein Ziel hat, wenn der gleiche Planet der nächste ist)
                for possible_planet in empty_planets_by_distance:
                    if possible_planet not in planned_planets:
                        target_planet = possible_planet
                        break

            if ship.can_dock(target_planet): command_queue.append(ship.dock(target_planet))
            else: fly_to(ship, target_planet)
            planned_planets.append(target_planet) # ausgewählten Planeten zur Liste der Planeten, die angeflogen werden, hinzufügen

        else:  # Schiffe angreifen und die Planeten einnehmen
    
            # target_ship = enemy_ships_by_distance[0]
            target_ship: hlt.entity.Ship

            first_ship, sec_ship = enemy_ships_by_distance[0], None
            first_ship: hlt.entity.Ship
            sec_ship: hlt.entity.Ship

            ships_assigned_to_target_ship_amount = int(ships_assigned_to_target_ship.get(first_ship.id, 0))
            max_amount = math.ceil(len(own_ships) / len(enemy_ships_by_distance))

            if ships_assigned_to_target_ship_amount < max_amount:

                for possible_ship in enemy_ships_by_distance:
                    possible_ship: hlt.entity.Ship

                    logging.info("Mögliches Schiff überprüfen")

                    if int(ships_assigned_to_target_ship.get(possible_ship.id, 0)) < max_amount:
                        sec_ship = possible_ship
                        logging.info("Zweites Schiff gefunden")
                        break

            # elif ships_assigned_to_target_ship_amount == max_amount:
            else:
                logging.info("Neues Schiff muss gesucht werden")

                for possible_ship in enemy_ships_by_distance:
                    possible_ship: hlt.entity.Ship

                    logging.info("Mögliches Schiff überprüfen")

                    if int(ships_assigned_to_target_ship.get(possible_ship.id, 0)) < max_amount:
                        if first_ship is None:
                            first_ship = possible_ship
                            logging.info("Erstes Schiff gefunden")
                        else:
                            sec_ship = possible_ship
                            logging.info("Zweites Schiff gefunden")
                            break

            logging.info("Schiff wird angegriffen...")
            target_ship = fly_to(ship, first_ship)

            if target_ship is not None:
                ships_assigned_to_target_ship.update({target_ship.id: int(ships_assigned_to_target_ship.get(target_ship.id, 0)) + 1})

            logging.info(ships_assigned_to_target_ship)

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
