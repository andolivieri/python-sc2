import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.player import Human

class ProxyRaxBot(sc2.BotAI):
    def select_target(self):
        target = self.known_enemy_structures
        if target.exists:
            return target.random.position

        target = self.known_enemy_units
        if target.exists:
            return target.random.position

        if min([u.position.distance_to(self.enemy_start_locations[0]) for u in self.units]) < 5:
            return self.enemy_start_locations[0].position

        return self.state.mineral_field.random.position

    async def on_step(self, iteration):
        cc = self.units(UnitTypeId.COMMANDCENTER)
        if not cc.exists:
            target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(UnitTypeId.CYCLONE):
                await self.do(unit.attack(target))
            return
        else:
            cc = cc.first

        if iteration % 50 == 0 and self.units(UnitTypeId.CYCLONE).amount > 2:
            target = self.select_target()
            forces = self.units(UnitTypeId.CYCLONE)
            if (iteration//50) % 10 == 0:
                for unit in forces:
                    await self.do(unit.attack(target))
            else:
                for unit in forces.idle:
                    await self.do(unit.attack(target))

        if self.can_afford(UnitTypeId.SCV) and self.workers.amount < 22 and cc.is_idle:
            await self.do(cc.train(UnitTypeId.SCV))

        elif self.supply_left < 3:
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

        if self.units(UnitTypeId.SUPPLYDEPOT).exists:
            if not self.units(UnitTypeId.BARRACKS).exists:
                if self.can_afford(UnitTypeId.BARRACKS):
                    await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

            elif self.units(UnitTypeId.BARRACKS).exists and self.units(UnitTypeId.REFINERY).amount < 2:
                if self.can_afford(UnitTypeId.REFINERY):
                    vgs = self.state.vespene_geyser.closer_than(20.0, cc)
                    for vg in vgs:
                        if self.units(UnitTypeId.REFINERY).closer_than(1.0, vg).exists:
                            break

                        worker = self.select_build_worker(vg.position)
                        if worker is None:
                            break

                        await self.do(worker.build(UnitTypeId.REFINERY, vg))
                        break

            if self.units(UnitTypeId.BARRACKS).ready.exists:
                if self.units(UnitTypeId.FACTORY).amount < 3 and not self.already_pending(UnitTypeId.FACTORY):
                    if self.can_afford(UnitTypeId.FACTORY):
                        p = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                        await self.build(UnitTypeId.FACTORY, near=p)

        for factory in self.units(UnitTypeId.FACTORY).ready.idle:


            if self.can_afford(UnitTypeId.FACTORYTECHLAB):
                await self.do(factory.build(UnitTypeId.FACTORYTECHLAB))
            # Reactor allows us to build two at a time
            if self.can_afford(UnitTypeId.CYCLONE):
                await self.do(factory.train(UnitTypeId.CYCLONE))

        for a in self.units(UnitTypeId.REFINERY):
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w.exists:
                    await self.do(w.random.gather(a))

        for scv in self.units(UnitTypeId.SCV).idle:
            await self.do(scv.gather(self.state.mineral_field.closest_to(cc)))

def main():
    sc2.run_game(sc2.maps.get("Port Aleksander LE"), [
        # Human(Race.Terran),
        Bot(Race.Terran, ProxyRaxBot()),
        Computer(Race.Zerg, Difficulty.Easy)
    ], realtime=False)

if __name__ == '__main__':
    main()
