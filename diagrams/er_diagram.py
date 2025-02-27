from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom

with Diagram("Menocare ER Diagram", show=False, direction="LR"):
    with Cluster("Database Schema"):
        users = Custom("users", "./icons/table.png")
        mood_tracker = Custom("mood_tracker", "./icons/table.png")
        nutrition_plan = Custom("nutrition_plan", "./icons/table.png")
        exercise_tracking = Custom("exercise_tracking", "./icons/table.png")
        hormonal_metrics = Custom("hormonal_metrics", "./icons/table.png")

        users >> Edge(label="1:N") >> mood_tracker
        users >> Edge(label="1:N") >> nutrition_plan
        users >> Edge(label="1:N") >> exercise_tracking
        users >> Edge(label="1:N") >> hormonal_metrics
