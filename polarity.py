from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import networkx as nx
import numpy as np
import os

class UserModel(Agent):
    def __init__(self, unique_id, model, group, tweet_probability):
        super().__init__(unique_id, model)
        self.followers = set()
        self.tweets = []
        self.group = group
        self.tweet_probability = tweet_probability
        self.contributors = []

    def step(self):
        # User behavior
        if self.random.random() < self.tweet_probability:
            tweet_content = f"Tweet from User {self.unique_id} in Group {self.group}!"
            contributors = self.model.get_contributors()  # Get the list of contributors from the model
            tweet_polarity = self.random.choice(["Group_A", "Group_B"])  # Randomly assign tweet to Group A or Group B
            tweet_agent = TweetModel(self.model.next_id(), self.model, tweet_content, contributors, tweet_polarity)
            self.model.schedule.add(tweet_agent)
            x = self.random.randrange(self.model.grid.width)
            y = self.random.randrange(self.model.grid.height)
            self.model.grid.place_agent(tweet_agent, (x, y))
            self.tweets.append(tweet_agent)

class TweetModel(Agent):
    def __init__(self, unique_id, model, content, contributors, polarity):
        super().__init__(unique_id, model)
        self.content = content
        self.contributors = contributors  # Store the list of contributors for the tweet
        self.polarity = polarity  # Store the tweet polarity

    def step(self):
        # Tweet behavior
        # Define any behavior related to tweets, e.g., a limited lifespan
        pass

class ContributorModel(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class SocialMediaModel(Model):
    def __init__(self, num_users, num_contributors, adjacency_matrix_file, tweet_probability=0.1):
        super().__init__()
        self.num_users = num_users
        self.num_contributors = num_contributors
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(num_users, num_users, True)

        # Create a DataCollector to collect data during the simulation
        self.datacollector = DataCollector(
            agent_reporters={"Followers": lambda a: len(a.followers) if hasattr(a, 'followers') else 0,
                             "Tweets": lambda a: len(a.tweets) if hasattr(a, 'tweets') else 0}
        )

        # Create users and add them to the grid, assigning them to Group A or Group B
        for i in range(num_users):
            group = "Group_A" if i < num_users // 2 else "Group_B"
            user_agent = UserModel(str(i), self, group, tweet_probability)
            self.schedule.add(user_agent)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(user_agent, (x, y))

        # Create tweets
        for i in range(num_users):
            tweet_polarity = self.random.choice(["Group_A", "Group_B"])
            tweet_agent = TweetModel(str(i + num_users), self, f"Tweet #{i}", [], tweet_polarity)
            self.schedule.add(tweet_agent)

        # Create contributors and add them to the schedule
        for i in range(num_contributors):
            contributor_agent = ContributorModel(str(i + num_users * 2), self)
            self.schedule.add(contributor_agent)

        # Load adjacency matrix from file
        adjacency_matrix = self.load_adjacency_matrix(adjacency_matrix_file)

    def load_adjacency_matrix(self, file_path):
        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file '{file_path}' does not exist.")

        # Load the adjacency matrix from the file
        with open(file_path, 'r') as file:
            lines = file.readlines()
            adjacency_matrix = [list(map(int, line.split())) for line in lines]

        # Create a directed graph from the adjacency matrix
        G = nx.DiGraph(np.array(adjacency_matrix))

        # Add followings between users based on the directed graph
        for edge in G.edges():
            follower_id, following_id = map(str, edge)

        # Find the follower agent
            follower = next((agent for agent in self.schedule.agents if agent.unique_id == follower_id), None)
            if follower is None:
                print(f"Warning: No agent found with unique_id {follower_id}")

        # Find the following agent
            following = next((agent for agent in self.schedule.agents if agent.unique_id == following_id), None)
            if following is None:
                print(f"Warning: No agent found with unique_id {following_id}")

        # Add the following to the followers
            if follower is not None and following is not None:
                follower.followers.add(following)
            
        return adjacency_matrix

    def get_contributors(self):
        return [agent for agent in self.schedule.agents if isinstance(agent, ContributorModel)]

    def step(self):
        self.schedule.step()

        for agent in self.schedule.agents:
            if isinstance(agent, UserModel):
                self.datacollector.collect(self)

        print("Current Step: ", self.schedule.time)
        print("Number of Agents: ", len(self.schedule.agents))

# Example usage
num_users = 130
num_contributors = 10
document_directory = f'C:/Users/radif/Documents/mesa'
adjacency_matrix_file = os.path.join(document_directory, 'adjtry.txt')
tweet_probability = 0.1

model = SocialMediaModel(num_users, num_contributors, adjacency_matrix_file, tweet_probability)
for i in range(10):
    model.step()
    print(f"Step {i + 1}")
    print("User-Followers:")
    for agent in model.schedule.agents:
        if isinstance(agent, UserModel):
            print(f"User {agent.unique_id} in Group {agent.group}: {len(agent.followers)} followers, {len(agent.tweets)} tweets")
    print("-------------")
