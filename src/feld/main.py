import os
import time
import random
import textwrap
import sys

# config
START_LUX = 10000
CYCLES_TOTAL = 50

HAB_COST = 50000
SUPPLY_COST = 500
SUPPLY_START = 20
SUPPLY_CONS = 1

temp_babble = ""

# utility
def clear():
    os.system("cls" if os.name == "nt" else "clear") # probably better to use escape chars

def format_text(text: str, codes: list) -> str:  # use ascii escapes natively instead of heavy dependent modules
    # codes: list of either color code or a tuple with (background: bool, int, int, int)
    colors = {
        # terminal utility codes
        "reset": "\x1b[0m",
        "home": "\x1b[H",
        "clear": "\x1b[2J",
        "clearline": "\x1b[2K",
        
        # formatting codes
        "bold": "\x1b[1m",
        "italic": "\x1b[3m",
        "underline": "\x1b[4m",
        "blinking": "\x1b[5m",
        "inverse": "\x1b[7m",
        "strikethrough": "\x1b[9m",
        
        # colors
        "red": "\x1b[31m",
        "yellow": "\x1b[33m",
        "green": "\x1b[32m",
        "cyan": "\x1b[36m",
        "blue": "\x1b[34m",
        "magenta": "\x1b[35m",
        "white": "\x1b[37m",
        "black": "\x1b[30m",
        "default": "\x1b[m",
        
        # bright colors
        "bright_black": "\x1b[90m",
        "bright_red": "\x1b[91m",
        "bright_green": "\x1b[92m",
        "bright_yellow": "\x1b[93m",
        "bright_blue": "\x1b[94m",
        "bright_magenta": "\x1b[95m",
        "bright_cyan": "\x1b[96m",
        "bright_white": "\x1b[97m",
    }
    
    buffer = ""
    if not isinstance(codes, list):
        raise TypeError(f"'codes' should be a list, even if with only one element. Found {type(codes)} instead.")
    if not isinstance(text, str):
        raise TypeError(f"'text' should be a string, found {type(text)} instead.")
    
    for code in codes:
        if isinstance(code, str):
            buffer += colors.get(code,"")
            
        elif isinstance(code, tuple):
            if not isinstance(code[0], bool):
                raise ValueError(f"Should be bool defining whether this is a background color, found {type(code[0])} instead.")
            if len(code) != 4:
                raise ValueError(f"Tuple should have four elements: (bool, r, g, b), found {len(code)}.")
            for i in code[1:]:
                if not isinstance(i, int):
                    raise ValueError(f"RGB must be integers, found {type(i)}.")
                if not (0 <= i <= 255):
                    raise ValueError(f"RGB numbers should be under 255 and at least 0, found {i} instead")
                
            final = f"\x1b[{48 if code[0] else 38};2;{code[1]};{code[2]};{code[3]}m"
            buffer += final
            
        else:
            raise TypeError(f"List 'codes' should only contain strings or tuples, found {type(code)} instead.")
        
    return f"{buffer}{text}{colors['reset']}"

def glitch(text: str, intensity: float, glitch_characters: str = "#$@%&^/?X") -> str:
    # TODO: Add unicode? lookalike table?
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < intensity:
            chars[i] = random.choice(glitch_characters)
    return "".join(chars)

GRAPH_CHARS = "▁▂▃▄▅▆▇█"
def sparkline(history, width = 20):
    if not history:
        return ""
    
    vals = history[-width:]
    lo, hi = min(vals), max(vals)
    n = len(vals)
    
    if hi - lo < 1e-9:
        return "".join(format_text(GRAPH_CHARS[0], ["yellow"]) for _ in vals)
    
    span = hi - lo
    scaled = [(v - lo) / span for v in vals]
    idxs = [int(s * (len(GRAPH_CHARS) - 1)) for s in scaled]

    parts = []
    for i in range(n):
        if i == 0:
            delta = 0
        else:
            delta = vals[i] - vals[i - 1]
        if abs(delta) < 0.05:
            col = "bright_yellow"
        elif delta > 0:
            col = "bright_green"
        else:
            col = "bright_red"
        
        ch = GRAPH_CHARS[idxs[i]]
        parts.append(format_text(ch, [col]))
    for _ in range(10 - len(parts)):
        parts.append(" ")
    return "".join(parts)

# classes
class Asset: # subclass to be used only under Market
    def __init__(self, id, name, base, volatility, resilience = 1.0):
        self.id = id
        self.name = name
        self.price = base
        self.volatility = volatility # How much asset is allowed to fluctuate
        self.resilience = float(resilience) if resilience > 0 else 1.0 # how easily it will decay, commonness of bursts
        self.trend = random.uniform(-0.05, 0.05) # keeps believable strings of up and down
        self.last_change = 0.0  # For stock ticker
        self.history = [self.price]
        self.delisted = False
        self.t = 0
        
    def update(self, stability: float):
        self.t += 1
        prev = self.price

        if self.delisted:
            self.price = 0.0
            self.last_change = 0.0
            return

        trend_change = random.uniform(-0.02, 0.02)
        self.trend += trend_change

        decay_factor = (1.0 - stability) ** 2 # Add pressure to drop as stability drops
        if stability < 0.06:
            decay_factor = 69.420
        sensitivity = decay_factor * (0.4 / self.resilience) # Scale by asset resilience
        trend_force = self.trend * (0.6 + 0.4 * stability) # Trend up or down so it's not super random
        random_fluct = random.uniform(-self.volatility, self.volatility) # Standard fluctuations
        burst = 0.0 # occasional burst to keep it alive
        if random.random() < 0.1 and stability < 0.6:
            burst = random.uniform(0.01, 0.2) # 

        delta_pct = trend_force - sensitivity + random_fluct + burst
        
        self.decay_factor, self.sensitivity, self.trend_force, self.random_fluct, self.burst, self.delta_pct = decay_factor, sensitivity, trend_force, random_fluct, burst, delta_pct
        # for debug, never actually used
        
        self.price = max(0.0, self.price * (1.0 + delta_pct))
        self.last_change = self.price - prev
        self.history.append(self.price)
        
        if self.price <= 0.5:
            self.price = 0.0
            self.delisted = True

class Market:
    def __init__(self):
        self.assets = [ # TODO: Add json parsing here
            Asset(1, "Helios Corp.", 8000, 0.02, 1.2), # name, base, volatility, resilience
            Asset(2, "MacroHard", 1111, 0.015, 1.0),
            Asset(3, "Michaelsoft Binbows", 2422, 0.01, 0.9),
            Asset(4, "Ionic Compound Manufacturers", 3500, 0.012, 1.1),
            Asset(5, "ClosedAI", 10000, 0.3, 0.3),
            Asset(6, "Photonic Semiconductors Ltd", 4200, 0.02, 1.0),
            Asset(7, "Super Earth Warbonds", 6969, 0.04, 1.3),
            Asset(8, "Lithium Mining Associates", 5000, 0.025, 0.9),
            Asset(9, "Tux", 10, 0.1, 1.5),
            Asset(10, "Richard Bored Private Reserve", 1000, 0.005, 1.2),
            Asset(11, "FICSIT, INC.", 4242, 0.03, 1.15)
        ]
        self.cycle = 0
    
    def tick(self):
        stability = self.target_stability(self.cycle)

        for a in self.assets:
            a.update(stability)
        self.cycle += 1
        
    def target_stability(self, cycle):
       t = cycle / CYCLES_TOTAL
       stability = 1.0 - t ** 2.8
       return max(0.0, min(1.0, stability))

    def getname(self, id): # surely there's a better way to do this
        for a in self.assets:
            if str(a.id) == id: # it was an integer
                return a.name
        raise ValueError
    
    def summary(self, player):
        print("┌────────────────────────────────────────────────────────────────────────┐")
        babble = textwrap.wrap(get_technobabble(), width = 70)
        for i in babble:
            print(f"│ {i:70} │")
        if len(babble) == 1: # so it doesnt "bounce"
            print("│                                                                        │")
        print( "╞═══════════╤═════════════╤═══════════════╤═════════════════╤════════════╡")
        print(f"│ [ Cycle ] │ [ Rations ] │ [ Ⱡ Account ] │ [ Ⱡ Net Worth ] │ ⣏⡉ ⣏⡉ ⡇ ⡏⢱ │\n│ [{self.cycle:^7}] │ [{player.supplies:^9}] │ [{round(player.lux):^11}] │ [{player.get_worth(self):^13}] │ ⠇⠀ ⠧⠤ ⠧ ⠧⠜ │")
        print( "╞═══════════╧═════════════╧════════╤══════╧═════════════════╪════════════╡")

        for a in self.assets:
            col = "red" if a.delisted else "bright_green" if a.last_change > 0 else "bright_red" if a.last_change < 0 else "yellow"
            sym = "╳" if a.delisted else "⌃" if a.last_change > 0 else "⌄" if a.last_change < 0 else "~"
            if a.delisted:
                price = " [BKRP] "
            else:
                price = f"{a.price:8.2f}"
            if a.last_change > 0:
                last_change = f"+{a.last_change:.0f}"
            else:
                last_change = f"{a.last_change:8.2f}"
            print(f"│ {a.id:2} {a.name:29} │ {format_text(f"{sym} {last_change:>8}", [col])}", format_text(f"(Ⱡ{price})", [col]), "│", f"{sparkline(a.history, width = 10)} │")
            
            if False: # DEBUG
                print(
                    "trend: ", str(round(a.trend, 4)).ljust(10),
                    "    decay: ", str(round(a.decay_factor, 4)).ljust(10),
                    "\nsnsvy: ", str(round(a.sensitivity, 4)).ljust(10),
                    "    tfrce: ", str(round(a.trend_force, 4)).ljust(10),
                    "\nfluct: ", str(round(a.random_fluct, 4)).ljust(10),
                    "    burst: ", str(round(a.burst, 4)).ljust(10), "\n")

class Player:
    def __init__(self):
        self.lux = START_LUX
        self.holdings = { }
        self.supplies = SUPPLY_START
        self.alive = True
        
    def add_asset(self, id, num):
        if id in self.holdings:
            self.holdings[id] += num
        else:
            self.holdings.setdefault(id, num)

    def get_worth(self, market):
        total = int(self.lux)
        for id, qty in self.holdings.items():
            a = next((x for x in market.assets if str(x.id) == id), None)
            if a:
                total += a.price * int(qty)
        return round(total)

    def consume(self, market):
        self.supplies -= SUPPLY_CONS
        if self.supplies == 1:
            get_technobabble(format_text("You only have one bag of supplies left. Better get on that.", ["bright_red"]))
        elif self.supplies == 0:
            game_end(self, market, starved=True)
            self.alive = False
    
    def inventory(self, market):
        clear()
        print("┌───────────────────────────────┬─────────────────┐") # WHAT THE FUCK
        print("│            Player             │   ⣏⡉ ⣏⡉ ⡇⠀ ⡏⢱   │")
        print("│           Portfolio           │   ⠇⠀ ⠧⠤ ⠧⠤ ⠧⠜   │")
        print("├───────────────────────────────┼─────────────────┤")
        if not self.holdings:
            total_value = 0 
            print("│ No Assets                     │ ", format_text("Ⱡ0.00", ["bright_red"]), "         │")
            print("├───────────────────────────────┴─────────────────┤")
            print(f"│ Portfolio value: Ⱡ{total_value:12.2f}                  │")
        else:
            total_value = 0
            for id, qty in self.holdings.items():
                asset = next((a for a in market.assets if str(a.id) == id), None)
                if asset:
                    value = asset.price * qty
                    total_value += value
                    print(f"│ {asset.name:30}│ {qty:3} @ Ⱡ{asset.price:8.2f} │")
            print("├───────────────────────────────┴─────────────────┤")
            print(f"│ Portfolio value: Ⱡ{total_value:12.2f}                  │")
        
        print("└─────────────────────────────────────────────────┘")

# logic
def get_technobabble(content = None):
    global temp_babble
    if content:
        temp_babble = content
        return None
    babble = [
        "NEWS: ⱠLux market collapse killing thousands of kittens and puppies.",
        "F.E.L.D announcement: Ⱡ Ⱡ Ⱡ Ⱡ Ⱡ Ⱡ Ⱡ Ⱡ",
        "NEWS: Civil war is brewing, which would only drain our ⱠLux reserves.",
        "NEWS: Habitat 22 is now taking applications via your local F.E.L.D. indentured servitude facility.",
        "NEWS: Man tasked with repairing the Dyson Sphere reportedly burns up in sun.",
        "NEWS: Failed to get today's news.",
        "Did you know? Technobabble like this is just generated off an array.",
        "NWES: That word was misspeled.",
        "NEWS: New AI tech startup ClosedAI eats massive ⱠLux costs, citizens upset.",
        "F.E.L.D notice: Indentured servitude workers will be discharged at the thought of using the bathroom.",
        "NEWS: Invest in the ⱠLux market before it collapses completely, experts claim.",
        "New podcast from the makers of 'The Grindset' reportedly places huge emphasis on roller blading.",
        "News from Earth: Widespread chaos. Citizens are urged to immediately harvest alien artifacts.",
        "Did I ever tell you about the time when?",
        "NEWS: Eminem resurrected only for him to reverse the action himself when seeing the state of the world.",
        "PSA: Be advised that software claiming to trade ⱠLux for you likely steal any rare gains.",
        "NEWS: It's never too late to switch to Linux. Going to be a challenge to power it, though.",
        "F.E.L.D notice: Level 4 executive bathrooms are currently under rennovation.",
        "NEWS: What did the mildly radioactive raccoon say? A question stumping genius babies worldwide.",
        "F.E.L.D stock ticker: ▁▁▂▂▃▃▄▄▅▅▆▆▇▇██, all day, every day.",
        "",
    ]
    if temp_babble:
        temp = temp_babble
        temp_babble = ""
        return temp
    else:
        random.shuffle(babble)
        return babble[1]

def game_end(player, market, starved = False):
    if starved:
        get_technobabble(format_text("You've run out of supplies and perished.", ["red"])) # EXPAND, OBVIOUSLY 
        
def handle_buy(player, market, arg):
    args = arg.strip().split()
    if len(args) < 2:
        print("Usage: buy <#> <id>")
        return False
    try:
        num = abs(int(args[0]))
        id = args[1]
    except ValueError:
        print("Invalid number, try again.")
        return False
    
    asset = next((a for a in market.assets if str(a.id) == id and not a.delisted), None)
    if not asset:
        print("Asset either bankrupt or doesn't exist.")
        return False
    
    cost = asset.price * num
    if player.lux < cost:
        print("You don't have enough ⱠLux.")
        return False
    
    player.lux -= cost
    player.add_asset(id, num)
    print(f"\n\nBought {num} shares of {asset.name} for Ⱡ{cost:.2f}")
    return True

def handle_sell(player, market, arg):
    args = arg.split(" ")
    id, num = args[1], int(args[0])
    num = abs(num)
    for owned_id in list(player.holdings.keys()):
        if str(owned_id) == id:
            a = next((x for x in market.assets if str(x.id) == id), None)
            if not a:
                print("Asset not found")
                return False
            if player.holdings[owned_id] < num:
                print("Not enough shares to sell.")
                return False
            player.holdings[owned_id] -= num
            if player.holdings[owned_id] == 0:
                del player.holdings[owned_id]
            player.lux += a.price * num
            print(f"\n\nSold {num} shares of {a.name} for Ⱡ{a.price * num:.2f}")
            return True
    print("You don't own that asset.")
    return False

def handle_rations(player, arg):
    args = arg.strip().split()
    num = abs(int(args[0])) if args else 1
    cost = SUPPLY_COST * num
    if player.lux < cost:
        print("\n\nNot enough Lux to buy rations")
        return False
    player.lux -= cost
    player.supplies += num
    print(f"Purchased {num} rations for Ⱡ{cost}.")
    return True

def show_help():
    clear()
    print("┌───────────────┬───────────────────────┐") # WHAT THE FUCK
    print("│   Help Menu   │      ⣏⡉ ⣏⡉ ⡇⠀ ⡏⢱      │")
    print("│    Command    │      ⠇⠀ ⠧⠤ ⠧⠤ ⠧⠜      │")
    print("├───────────────┼───────────────────────┤")
    print("│ buy <#> <id>  │ Buy number of assets  │")
    print("│ sell <#> <id> │ Sell number of assets │")
    print("│ portfolio     │ View all your assets  │")
    print("│ rations <#>   │ Buy some supplies     │")
    print("│ wait [or w]   │ Go get some rest      │")
    print("│ lore          │ Get the game's lore   │")
    print("├───────────────┴───────────────────────┤")
    print("│ Every Cycle (archaic: Day) you, as a  │")
    print("│ Federal Energy Logistics Division     │")
    print("│ Indentured Servitude Empoyee (aka as  │")
    print("│ a FELD.ISE), will trade in the ⱠLux   │")
    print("│ market. After recent events, the ⱠLux │")
    print("│ market is falling - companies are now │")
    print("│ eating power when we cannot produce   │")
    print("│ any more. Your task is to reach a net │")
    print("│ worth of Ⱡ50,000 before all assets    │")
    print("│ go bankrupt. Only then will we (FELD) │")
    print("│ supply you with a pass to a FELD-HAB  │")
    print("│ (Habitation and Board) area, ensuring │")
    print("│ you survive until repairs on Sol Ark. │")
    print("└───────────────────────────────────────┘")
    
def lore():
    print("┌────────────────────────────────────────────────────────────────────────┐")
    print("│ In the year 2077, an asteroid known as 529556 Cabeiri was discovered   │")
    print("│ inside a pocket of dust halfway to Proxima Centauri. Inside, scans     │")
    print("│ revealed a huge mound of a previously undiscovered stable isotope of   │")
    print("│ Francium, sparking waves in the scientific community. It appears to be │")
    print("│ useful in many ways - first and foremost, its uncanny ability to fold  │")
    print("│ outward as if it were as thin as paper whilst also absorbing solar     │")
    print("│ energy. Scientists attempted to convince people to switch to panels on │")
    print("│ their homes, but people are stubborn; instead, we turned to the source.│")
    print("│                                                                        │")
    print("│ By 2108, scientists had prototyped and launched an interstellar probe. │")
    print("│ It was designed to attach to Cabeiri and extract Francium-339 whilst   │")
    print("│ operating on power harvested from an RTG. The probe, nicknamed Gaia,   │")
    print("│ then built tiny panels with tiny solar sails that would propel them to │")
    print("│ our sun and unfold, eventually forming a huge Dyson Sphere around Sol. │")
    print("│                                                                        │")
    print("│ In 2112, construction completed, and shipments of physical batteries   │")
    print("│ (also made from Francium) began periodically coming in from what we    │")
    print("│ decided to name the Sol Ark. Occasional solar flares forced Gaia to    │")
    print("│ replace panels, but the RTG retained just enough power to keep the Sol │")
    print("│ Ark active and producing power.                                        │")
    print("│                                                                        │")
    print("│ However, in the year 2195, a massive gash in the power delivery part   │")
    print("│ of the Sol Ark formed after a particularly large solar flare. The RTG  │")
    print("│ in Gaia had finally failed, and since we no longer had the exact parts │")
    print("│ needed to rebuild it, we are forced to send a new probe. Very quickly, │")
    print("│ a new probe was designed, constructed, and sent - but we were working  │")
    print("│ with tiny amounts of power (which we call Lux) left. The probe has     │")
    print("│ around a year left in its journey, so we just need to survive until it │")
    print("│ can get there and begin producing the very fast moving Ark fragments.  │")
    print("│                                                                        │")
    print("│ However, humanity doesn't like making things easy for itself. We had   │")
    print("│ started trading things with Lux (our power) as a type of currency -    │")
    print("│ now that no more could be produced, the market (and thus people's      │")
    print("│ supplies) was collapsing, resulting in the FALL of capitalism. (siege) │")
    print("│                                                                        │")
    print("│ Enter the Federal Energy Logistics Divison, or F.E.L.D. Their job was  │")
    print("│ to mediate the Lux market, but it is now to provide access to the      │")
    print("│ habitats that the government had created. F.E.L.D realised it needed a │")
    print("│ source of revenue, so what better way to get it than force potential   │")
    print("│ Habitat-dwellers to trade stocks for them in hopes that they would     │")
    print("│ earn a place to live whilst the Sol Ark was repopulated.               │")
    print("│                                                                        │")     
    print("│ As a FELD employee, you must secure your ticket in while surviving     │")
    print("│ the FALL of the market brought on by humanity's foolish decisions.     │")
    print("└────────────────────────────────────────────────────────────────────────┘")

def input_handler(the, player, market):
    the = the.lower()
    status = False
    if the.startswith("lore"):
        lore()
        input("[Enter]")
    elif the.startswith("exit") or the.startswith("quit"):
        print("\n\n")
        sys.exit(0)
    elif the.startswith("help"):
        show_help()
        input("[Enter]")
    elif the.startswith("buy"):
        status = handle_buy(player, market, the.removeprefix("buy "))
        input("[Enter]")
    elif the.startswith("sell"):
        status = handle_sell(player, market, the.removeprefix("sell "))
        input("[Enter]")
    elif the.startswith("wait") or the == "w":
        status = True
    elif the.startswith("inv") or the.startswith("portfolio"):
        player.inventory(market)
        input("[Enter]")
        status = False
    else:
        print("\n\nI don't recognize that command.")
        input("[Enter]")
    if status:
        return True
    else:
        return False

# loop
def main():
    market = Market()
    player = Player()
    market.tick()
    while(True):
        if market.cycle <= 1:
            get_technobabble("F.E.L.D notice: Try entering \"help\" if you feel lost.")
        clear()
        market.summary(player)
        print("╞══════════════════════════════════╧════════════════════════╧════════════╡")
        print("│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│", flush = True)
        print("└────────────────────────────────────────────────────────────────────────┘", end = "", flush = True)
        print("\x1b[1A\x1b[1G│ ", end = "", flush = True)
        status = input_handler(input(">"), player, market)
        if status: # iterate if they did something that modifies player (takes time)
            market.tick()
            player.consume(market)
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n")
        sys.exit(0)
