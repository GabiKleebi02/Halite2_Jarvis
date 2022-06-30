import hlt
import logging
from collections import OrderedDict
import math
from astar import AStar, Point

game = hlt.Game("Jarvis-v4")
logging.info("Starting my Jarvis bot")
pathfinder = None


# function to calculate if a Point p is in a line specified by two Points a and b
# @params: a, b     -   two points specifying a line
#           c       -   a Point tested if on the line
# @return: boolean  -   True, if point is on the line, False otherwise
def isInLine(a, b, p):
    v = hlt.entity.Position(0, 0)

    # Falls x-Werte gleich:
    if b.x == a.x:
        if b.y == a.y:
            logging.info(f"Die Punkte {a} und {b} sind verbotenerweise identisch!")
            print(f"Die Punkte {a} und {b} sind verbotenerweise identisch!")
        return abs(p.x - a.x) < 0.5

    # Falls nur y-Werte gleich:
    if b.y == a.y:
        return abs(p.y - a.y) < 0.5

    # Ansonsten finde den Schnittpunkt v der Geraden g und der Normalen zu g durch den Punkt p
    else:
        m = (b.y - a.y) / (b.x - a.x)                          # Steigung der Geraden g
        c = ((a.y * b.x) - (b.y * a.x)) / (b.x - a.x)          # Y-Achsenabschnitt von g
        n = -1 / m                                             # Steigung der Normalen zu g
        d = p.y - n * p.x                                      # Y-Achsenschnittpunkt der Normalen durch den Punkt p
        v.x = (d - c) / (m - n)                                # x-Wert des Schnittpunktes
        v.y = m * v.x + c                                      # y-Wert des Schnittpunktes
        dist = math.sqrt((p.x - v.x) ** 2 + (p.y - v.y) ** 2)  # Abstand der Punkte p und v (und damit zu g)
        return dist < 0.7  # Gebe True zurück, wenn der Abstand von p zu g kleiner als die Hälfte von Wurzel 2 ist


def fly_to_point(ship: hlt.entity.Ship, point: (int, int)):
    target = hlt.entity.Position(point[0], point[1])

    navigate_command = ship.navigate(
        target=target,
        game_map=game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False
    )

    if navigate_command:
        command_queue.append(navigate_command)


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



paths_for_ships = {}
    

while True:
    game_map = game.update_map()
    command_queue = []
    planned_planets = []
    ships_assigned_to_target_ship = {}

    if pathfinder is None:
        pathfinder = AStar(game_map)
    
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

            if ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
                paths_for_ships.pop(ship.id, None)
            else:
                path = paths_for_ships.get(ship.id, None)
                
                if not path:
                    logging.info(f"ship with id {int(ship.id)} needs new path")
                    point_x = target_planet.x + (target_planet.radius + 2) * math.cos(ship.calculate_angle_between(target_planet))
                    point_y = target_planet.y + (target_planet.radius + 2) * math.sin(ship.calculate_angle_between(target_planet))

                    path = pathfinder.find_path(int(ship.x), int(ship.y), int(point_x), int(point_y))
                    paths_for_ships.update({ship.id: path})
                
                fly_to_point(ship, path.pop(0))

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
