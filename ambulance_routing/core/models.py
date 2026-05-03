

from django.db import models


# ─────────────────────────────────────────────
# NODE — a single intersection/point on the map
# ─────────────────────────────────────────────
class Node(models.Model):
    # Human-readable label, e.g. "N_0_0" for row 0, col 0 of the grid
    label = models.CharField(max_length=50, unique=True)

    # GPS coordinates — used for the Leaflet map markers and A* heuristic
    latitude  = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.label} ({self.latitude:.4f}, {self.longitude:.4f})"


# ─────────────────────────────────────────────
# EDGE — a directed road segment between two nodes
# ─────────────────────────────────────────────
class Edge(models.Model):
    # ForeignKey creates a reference to another table row
    # on_delete=CASCADE means: if a Node is deleted, delete its edges too
    source      = models.ForeignKey(Node, related_name='outgoing_edges', on_delete=models.CASCADE)
    destination = models.ForeignKey(Node, related_name='incoming_edges', on_delete=models.CASCADE)

    # distance in km — used as the main edge weight for routing
    distance = models.FloatField()

    # travel time in minutes — alternative weight (used in some views)
    travel_time = models.FloatField()

    # Traffic multiplier — 1.0 = normal, 2.0 = double the weight
    # The Traffic Control page updates this value to simulate congestion
    traffic_weight = models.FloatField(default=1.0)

    def effective_weight(self):

        return self.distance * self.traffic_weight

    def __str__(self):
        return f"{self.source.label} → {self.destination.label} ({self.distance:.2f} km)"


# ─────────────────────────────────────────────
# HOSPITAL — a hospital located at a Node
# ─────────────────────────────────────────────
class Hospital(models.Model):
    name = models.CharField(max_length=100)

    # OneToOneField means: one hospital per node (unique)
    node = models.OneToOneField(Node, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# AMBULANCE — a vehicle stationed at a Node
# ─────────────────────────────────────────────
class Ambulance(models.Model):
    name = models.CharField(max_length=50)

    # Where the ambulance is currently stationed
    node = models.ForeignKey(Node, on_delete=models.CASCADE)

    # True = ready to dispatch, False = currently on a call
    is_available = models.BooleanField(default=True)

    def __str__(self):
        status = "available" if self.is_available else "busy"
        return f"{self.name} at {self.node.label} [{status}]"


# ─────────────────────────────────────────────
# EMERGENCY REQUEST — a logged dispatch event
# ─────────────────────────────────────────────
class EmergencyRequest(models.Model):
    # The node where the patient is located (clicked on the map)
    patient_node = models.ForeignKey(Node, related_name='emergencies', on_delete=models.CASCADE)

    # Which ambulance was dispatched
    ambulance = models.ForeignKey(Ambulance, null=True, blank=True, on_delete=models.SET_NULL)

    # Which hospital was selected as the destination
    hospital = models.ForeignKey(Hospital, null=True, blank=True, on_delete=models.SET_NULL)

    # Total route distance in km
    total_distance = models.FloatField(default=0)

    # When this request was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Emergency at {self.patient_node.label} — {self.created_at.strftime('%H:%M')}"
