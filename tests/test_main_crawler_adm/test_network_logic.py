import pytest
import random

# Define random mentions
def get_mentions(channel):
    mentions = [f"Mention_{random.randint(1, 100)}" for _ in range(random.randint(1, 5))]
    fwds = [random.randint(1000000000, 2000000000) for _ in range(random.randint(0, 3))]
    link = f"Link_{random.randint(1, 100)}" if random.random() < 0.5 else None
    return mentions, fwds, link

def test_full_iteration():
    chat_ids = [1318919825, 1123235006, 1635259727]
    full_iteration = {}

    for iteration_num in range(1, 4):
        all_mentions = []
        fwds = []
        link = None

        # Iterate over channels
        for chat_id in chat_ids:
            # Get random data from get_mentions function
            mentioned_chats_full, fwd_from_chats_full, linked_chat_id = get_mentions(chat_id)

            # Append the values of all mentioned chat types
            all_mentions.extend(mentioned_chats_full)
            all_mentions.extend(fwd_from_chats_full)
            if linked_chat_id is not None: 
                all_mentions.append(linked_chat_id)
            
            # Creating chat dictionary with mentioned chats
            all_mentions_dict = {
                "Mentioned": mentioned_chats_full,
                "Fwd_from": fwd_from_chats_full,
                "Linked": linked_chat_id,
            }
            
            # Appending chat dictionary to all chat dictionaries with mentioned chats from this iteration
            full_iteration.setdefault(f"iteration{iteration_num}", []).append(all_mentions_dict)

    # Assertions on the full_iteration dictionary
    assert isinstance(full_iteration, dict)
    assert len(full_iteration) == 3  # Check if there are 3 iterations

    # Check the structure of each iteration
    for iteration_num in range(1, 4):
        iteration_key = f"iteration{iteration_num}"
        assert iteration_key in full_iteration
        assert isinstance(full_iteration[iteration_key], list)

        # Check if each item in the iteration list is a dictionary
        for item in full_iteration[iteration_key]:
            assert isinstance(item, dict)

            # Check if each dictionary in the iteration has the expected keys
            assert "Mentioned" in item
            assert "Fwd_from" in item
            assert "Linked" in item

            # Check if the values of "Mentioned" and "Fwd_from" are lists
            assert isinstance(item["Mentioned"], list)
            assert isinstance(item["Fwd_from"], list)

            # Check if the value of "Linked" is either None or a string
            assert item["Linked"] is None or isinstance(item["Linked"], str)

# Run the test
test_full_iteration()