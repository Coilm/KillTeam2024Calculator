from dataclasses import dataclass
import numpy as np

@dataclass
class Attacker:
    name: str
    atk: int
    hit: int
    dmg: int
    critdmg: int
    keywords: list[str]
    lethal: int = 6
    piercing: int = 0
    devastating: int = 0
    
    def __post_init__(self):
        for keyword in self.keywords:
            if 'Lethal' in keyword:
                value = keyword.split(' ')[1][0]
                self.lethal = np.min([self.lethal, int(value)])
            if 'Dev' in keyword:
                self.devastating = int(keyword.split('Dev')[1])
            if 'Prc1' in keyword or 'Prc2' in keyword:
                self.piercing = int(keyword.split('Prc')[1])
                

@dataclass
class Defender:
    name: str
    save: int
    wounds: int
    cover: bool = False
    obscured: bool = False

class Simulation:
    def __init__(self, offensive_profile, defensive_profile, cover=False, obscured=False):
        self.attacker = Offensive(offensive_profile)
        self.defender = Defensive(defensive_profile, cover, obscured)
        if 'Saturate' in self.attacker.keywords:
            self.defender.cover=False

    def run(self, simstep=1):
        results = []
        atk_rolls = np.random.randint(1,7, (simstep,self.attacker.atk))
        def_rolls = np.random.randint(1,7, (simstep, 3))

        for atk_roll, def_roll in zip(atk_rolls, def_rolls):
            atk_success, atk_crit, _ = self.attacker.attack(atk_roll)

            if self.defender.obscured:
                atk_success += atk_crit
                atk_crit = 0

            def_success, def_crit, _ = self.defender.defend(roll=def_roll, piercing=self.attacker.piercing)

            results.append(self.resulting_damage(atk_success, atk_crit, def_success, def_crit))
        return np.array(results)
    
    def attack(self, atk_rolls):
        success = np.zeros(np.shape(atk_rolls)[0])
        crit = np.zeros(np.shape(atk_rolls)[0])
        fail = np.zeros(np.shape(atk_rolls)[0])

        for keyword in self.attacker.keywords:
            if 'Acc' in keyword:
                success += keyword.split('Acc')[1]
                atk_rolls = atk_rolls[:,:-1]
                break
    
        # Check for reroll keyword
        # TODO: Implement the reroll mechanic to do the whole set of rolls instead of just one
        '''
        for keyword in self.keywords:
            if keyword in ['Bal', 'Ceaseless', 'Relentless']:
                atk_rolls = self.reroll(atk_rolls, keyword)
        '''
        
        # Check for lethal
        crit += np.sum(atk_rolls >= self.attacker.lethal, axis = 1)

        success += np.sum((atk_rolls >= self.attacker.hit) & (atk_rolls < self.attacker.lethal), axis = 1)
        fail += self.attacker.atk - success - crit

        # Check for Severe:
        if ('Severe' in self.attacker.keywords):
            for idx in np.where(np.logical_and((crit == 0), (success >= 1))):
                success[idx] -= 1
                crit[idx] += 1

        # Check crit-based keyword
        if crit > 0:
            for keyword in self.keywords:
                if 'PrcCrit' in keyword:
                    self.piercing = np.max([self.piercing, int(keyword.split('PrcCrit')[1])])
                if 'Punishing' in keyword:
                    if fail > 0:
                        fail -= 1
                        success += 1
                if 'Rending' in keyword:
                    if success > 0:
                        success -= 1
                        crit += 1

        return success, crit, fail
    def defend():
        pass

    def resulting_damage(self, atk_success, atk_crit, def_success, def_crit):
        # Devastating
        damages = atk_crit * self.attacker.devastating

        while def_crit > 0:
            def_crit -= 1
            if (atk_crit > 0) and (atk_success > 0):
                if self.attacker.dmg > self.attacker.critdmg:
                    atk_success -= 1
                else:
                    atk_crit -= 1
            elif (atk_crit > 0) and (atk_success <= 0):
                atk_crit -= 1
            elif (atk_crit <= 0) and (atk_success > 0):
                atk_success -= 1

        if atk_crit <= 0 and atk_success <= 0:
            return damages
        
        while def_success > 0:
            if def_success >= 2:
                if atk_crit > 0 and atk_success < 2 and self.attacker.dmg <= self.attacker.critdmg:
                    def_success -= 1
                    atk_crit -= 1
                elif atk_crit > 0 and 2 * self.attacker.dmg <= self.attacker.critdmg:
                    def_success -= 1
                    atk_crit -= 1
                elif atk_success > 0:
                    atk_success -= 1
            else:
                if atk_success > 0:
                    atk_success -= 1
            def_success -= 1
        
        if atk_success < 0:
            print(f"ERROR ATK SUCCESS: {atk_success}")
        if atk_crit < 0:
            print(f"ERROR ATK CRIT: {atk_success}")

        damages += atk_success*self.attacker.dmg + atk_crit * self.attacker.critdmg

        return damages


class Offensive:
    def __init__(self, row):
        self.name = row['opname'] + ' - ' + row['wepname']
        self.atk = row['A']
        self.hit = row['BS']
        self.dmg = row['D']
        self.critdmg = row['DCrit']
        self.keywords = set(row['SR'])

        self.lethal = 6
        self.piercing = 0
        self.devastating = 0

        for keyword in self.keywords:
            if 'Lethal' in keyword:
                value = keyword.split(' ')[1][0]
                self.lethal = np.min([self.lethal, int(value)])
            if 'Dev' in keyword:
                self.devastating = int(keyword.split('Dev')[1])
            if 'Prc1' in keyword or 'Prc2' in keyword:
                self.piercing = int(keyword.split('Prc')[1])
   
    def attack(self, roll=None):
        success = 0
        crit = 0
        fail = 0

        if roll is None:
            # Check for accurate
            for keyword in self.keywords:
                if 'Acc' in keyword:
                    success += keyword.split('Acc')[1]
                    roll_value = self.atk - keyword.split('Acc')[1]
                    break
                else:
                    roll_value = self.atk
            atk_roll = np.array([np.random.randint(1,7) for _ in range(roll_value)])
        else:
            for keyword in self.keywords:
                if 'Acc' in keyword:
                    success += keyword.split('Acc')[1]
                    atk_roll = roll[:-1]
                    break
                else:
                    atk_roll = roll
                
        # Check for reroll keyword
        for keyword in self.keywords:
            if keyword in ['Bal', 'Ceaseless', 'Relentless']:
                atk_roll = self.reroll(atk_roll, keyword)

        # Check for lethal
        crit = np.count_nonzero(atk_roll >= self.lethal)

        success = np.count_nonzero((atk_roll >= self.hit) & (atk_roll < self.lethal))
        fail = self.atk - success - crit

        # Check for Severe:
        if (crit == 0) and ('Severe' in self.keywords) and (success > 0):
            success -= 1
            crit += 1

        # Check crit-based keyword
        if crit > 0:
            for keyword in self.keywords:
                if 'PrcCrit' in keyword:
                    self.piercing = np.max([self.piercing, int(keyword.split('PrcCrit')[1])])
                if 'Punishing' in keyword:
                    if fail > 0:
                        fail -= 1
                        success += 1
                if 'Rending' in keyword:
                    if success > 0:
                        success -= 1
                        crit += 1

        return success, crit, fail
    
    def reroll(self, roll, type='Bal'):
        # TODO: Implement better logic for multiple reroll keywords. 
        # BUG: So far the code DOES NOT work if there is multiple reroll keywords (It is possible to reroll an already rerolled dice.)

        if np.sum(roll < self.hit) == 0: # No fail
            return roll
        
        if type == 'Relentless':
            for idx in np.argwhere(roll < self.hit)[0]:
                roll[idx[0]] = np.random.randint(1,7)

        elif type == 'Ceasless':
            most_common = max([(roll.count(i), i) for i in set(roll[roll < self.hit])])[1]
            for idx in np.argwhere(roll == most_common)[0]:
                roll[idx[0]] = np.random.randint(1,7)

        elif type == 'Bal':
            idx = np.argwhere(roll < self.hit)[0]
            roll[idx[0]] = np.random.randint(1,7)    
        return roll



class Defensive():
    def __init__(self, row, cover=False, obscured=False):
        self.name = row['opname']
        self.save = row['SV']
        self.wounds = row['W']
        self.cover = cover
        self.obscured = obscured

    def defend(self, roll=None, piercing=0):
        num_dice = 3 - piercing
        success = 0
        crit = 0

        if self.cover and num_dice > 0:
            success += 1
            num_dice -= 1
        if roll is None:
            def_roll = np.array([np.random.randint(1,7) for _ in range(num_dice)])
        else:
            def_roll = roll[:num_dice]
        
        crit = np.count_nonzero(def_roll == 6)
        def_roll = def_roll[def_roll < 6]
        success += np.count_nonzero(def_roll >= self.save)

        fail = 3 - success - crit
        
        return success, crit, fail


class Simulation:
    def __init__(self, offensive_profile, defensive_profile, cover=False, obscured=False):
        self.attacker = Offensive(offensive_profile)
        self.defender = Defensive(defensive_profile, cover, obscured)
        if 'Saturate' in self.attacker.keywords:
            self.defender.cover=False
        
    def simulation_step(self, simstep=1):
        results = []
        atk_rolls = np.random.randint(1,7, (simstep,self.attacker.atk))
        def_rolls = np.random.randint(1,7, (simstep, 3))

        for atk_roll, def_roll in zip(atk_rolls, def_rolls):
            atk_success, atk_crit, _ = self.attacker.attack(atk_roll)

            if self.defender.obscured:
                atk_success += atk_crit
                atk_crit = 0

            def_success, def_crit, _ = self.defender.defend(roll=def_roll, piercing=self.attacker.piercing)

            results.append(self.resulting_damage(atk_success, atk_crit, def_success, def_crit))
        return np.array(results)


    def resulting_damage(self, atk_success, atk_crit, def_success, def_crit):
        # Devastating
        damages = atk_crit * self.attacker.devastating

        while def_crit > 0:
            def_crit -= 1
            if (atk_crit > 0) and (atk_success > 0):
                if self.attacker.dmg > self.attacker.critdmg:
                    atk_success -= 1
                else:
                    atk_crit -= 1
            elif (atk_crit > 0) and (atk_success <= 0):
                atk_crit -= 1
            elif (atk_crit <= 0) and (atk_success > 0):
                atk_success -= 1

        if atk_crit <= 0 and atk_success <= 0:
            return damages
        
        while def_success > 0:
            if def_success >= 2:
                if atk_crit > 0 and atk_success < 2 and self.attacker.dmg <= self.attacker.critdmg:
                    def_success -= 1
                    atk_crit -= 1
                elif atk_crit > 0 and 2 * self.attacker.dmg <= self.attacker.critdmg:
                    def_success -= 1
                    atk_crit -= 1
                elif atk_success > 0:
                    atk_success -= 1
            else:
                if atk_success > 0:
                    atk_success -= 1
            def_success -= 1
        
        if atk_success < 0:
            print(f"ERROR ATK SUCCESS: {atk_success}")
        if atk_crit < 0:
            print(f"ERROR ATK CRIT: {atk_success}")


        damages += atk_success*self.attacker.dmg + atk_crit * self.attacker.critdmg

        return damages