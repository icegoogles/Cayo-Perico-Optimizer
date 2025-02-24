def backend_optimizer(nr_available, nr_players):
    # value per stack
    value_per_stack = {
        "Cash":  85,
        "Artw":  185,
        "Weed":  145,
        "Koka":  220,
        "Gold":  330,
    }   

    # Maximum parts per stack (in how many parts the stack can split)
    stacksplit = {
        "Cash":  4,
        "Artw":  1,
        "Weed":  4,
        "Koka":  4,
        "Gold":  4
    }

    #Gewicht, Wert
    values = {
        "Cash":  [(1/4) / stacksplit["Cash"],  nr_available["Cash"] * stacksplit["Cash"]],
        "Artw":  [(1/2) / stacksplit["Artw"],  nr_available["Artw"] * stacksplit["Artw"]],
        "Weed":  [(1/3) / stacksplit["Weed"],  nr_available["Weed"] * stacksplit["Weed"]],
        "Koka":  [(1/2) / stacksplit["Koka"],  nr_available["Koka"] * stacksplit["Koka"]],
        "Gold":  [(2/3) / stacksplit["Gold"],  nr_available["Gold"] * stacksplit["Gold"]]
    }

    # try to get stuff in this order
    best_to_worst = ["Gold", "Koka", "Weed", "Artw", "Cash"]

    ##########  Optimzer  #########

    def distribute_items(values, best_to_worst, num_players=4):
        players = [0] * num_players  # Jeder Spieler kann max. Gewicht 1.0 tragen
        inventory = [{} for _ in range(num_players)]
        
        for item in best_to_worst:
            weight, quantity = values[item]
            
            for _ in range(quantity):
                for i in range(num_players):
                    if players[i] + weight <= 1.0:  # Prüfen, ob der Spieler noch Platz hat
                        players[i] += weight
                        if item in inventory[i]:
                            inventory[i][item] += 1
                        else:
                            inventory[i][item] = 1
                        break  # Sobald ein Spieler das Item nimmt, weiter zum nächsten Item
        
        return inventory


    # Multiply elements for all keys
    products = {key: values[0] * values[1] for key, values in values.items()}
    total_stuff = sum(products.values())

    print(products)
    print(f"Total bags available: {total_stuff:.3f}\n")

    ### main optimizer

    distributed_inventory = distribute_items(values, best_to_worst, nr_players)
    for i, items in enumerate(distributed_inventory, 1):
        item_list = ", ".join(f"{item} x{count/stacksplit[item]}" for item, count in items.items())
        print(f"Spieler {i}: {item_list}")

    # convert to stack-unit
    for player in distributed_inventory:
        for item in list(player.keys()):  # Iterate over keys while modifying
            player[item] /= stacksplit[item]  # Divide by stack size

    # add none if the item was not taken
    required_keys = ["Gold", "Koka", "Weed", "Artw", "Cash"]
    for player in distributed_inventory:
        for key in required_keys:
            player.setdefault(key, None)

    # calc value for each player
    accumulate_value = 0

    for player in distributed_inventory:

        player_value = 0
        for item in list(player.keys()):  # Iterate over keys while modifying
            if player[item] is None: continue
            player_value += player[item]*value_per_stack[item]  # approx. value of each item
        
        player["OwnValue"] = player_value

        accumulate_value += player_value
        player["AccumValue"] = accumulate_value

    return distributed_inventory
    

###############################################
########## STREAMLIT Application ##############
###############################################


import streamlit as st
import pandas as pd


location_options = ["Start House", "Pool House", "Main Quest/Office", "Shitty Mid House", "Runway"]


if 'data_overview' not in st.session_state:
    st.session_state.data_overview = pd.DataFrame(
        {
            "Location": location_options,
            "Gold": [0,0,0,0,0], 
            "Cocaine": [0,0,0,0,0], 
            "Weed": [0,0,0,0,0], 
            "Artwork": [0,0,0,0,0], 
            "Cash": [0,0,0,0,0]
        }
    )

    st.session_state.result_pd = pd.DataFrame()

data = st.session_state.data_overview
#result_pd = st.session_state.result_pd

st.title("Cayo Perico Optimizer!")

number_of_players = st.number_input(
    "Insert number of players", value=4, placeholder="Type a number...", min_value=1, max_value=4
)

st.write("Add new loot:")

col1, col2, col3 = st.columns([1,1,1])
with col1:
    locations = st.radio(
        "Location:", location_options,
    )

with col2:
    loot_types = st.radio(
        "Loot Type:",
        ["Gold", "Cocaine", "Artwork", "Weed", "Cash"]
    )

with col3:            
    # Every form must have a submit button.
    col31, col32 = st.columns([1,1])

    def added_item():
        st.session_state.data_overview.at[location_options.index(locations), loot_types] += 1

    def subtract_item():
        if (data.at[location_options.index(locations), loot_types] <= 0): return  # not allow below 0
        data.at[location_options.index(locations), loot_types] -=1


    with col31:
        added = st.button("add", on_click=added_item)
    with col32:
        subtracted = st.button("subtract", on_click=subtract_item)

    
    toggle_use_mid_house = st.toggle("Use Shitty Mid House", value=False)
    toggle_use_runway =    st.toggle("Use runway", value=True)



# plot data
st.write(data)

def optimize_loot():
    print("Optimizing...")
    
    data_copy = data.copy()
    
    if(data_copy is not None and toggle_use_mid_house == False):
        data_copy = data_copy.drop(location_options.index("Shitty Mid House"), inplace=True)
    
    if(data_copy is not None and toggle_use_runway == False):
        data_copy = data_copy.drop(location_options.index("Runway"), inplace=True)

    gold_available = data["Gold"].sum()
    coca_available = data["Cocaine"].sum()
    weed_available = data["Weed"].sum()
    artw_available = data["Artwork"].sum()
    cash_available = data["Cash"].sum()
            
    nr_available = {
        "Cash":  cash_available,
        "Artw":  artw_available,
        "Weed":  weed_available,
        "Koka":  coca_available,
        "Gold":  gold_available,
    }

    result = backend_optimizer(nr_available, number_of_players)

    st.session_state.result_pd = pd.DataFrame.from_dict(result)  # write to session state

    

st.button('Optimize!', on_click=optimize_loot)

placeholder_for_result = st.empty()

# Use the placeholder to display the result
if st.session_state.result_pd is not None:
    with placeholder_for_result:
        st.write("### Final Result")
        st.write(st.session_state.result_pd)

if __name__ == "__main__":
    pass