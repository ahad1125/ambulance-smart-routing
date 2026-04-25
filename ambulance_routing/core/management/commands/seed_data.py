"""
core/management/commands/seed_data.py

PURPOSE:
  Populates the database with a realistic road network for the Smart Ambulance
  project. Creates nodes (intersections), edges (roads), hospitals, and ambulances.

  Run with:  python manage.py seed_data

HOW THE GRAPH IS STRUCTURED:
  We create a 6×6 grid of intersections (36 nodes) representing a simplified
  city road network in Rawalpindi/Lahore area.

  Hospitals are placed at specific grid intersections.
  Ambulances are stationed near the centre of the grid.

  Grid spacing ≈ 0.01 degrees lat/lon ≈ 1.1 km per cell.
  Base lat/lon: Rawalpindi area (33.6, 73.0)
"""

from django.core.management.base import BaseCommand
from core.models import Node, Edge, Hospital, Ambulance
import math
import random


class Command(BaseCommand):
    help = 'Seeds the database with a city road network, hospitals, and ambulances'

    def handle(self, *args, **options):
        random.seed(42)  # Deterministic seed so the same city is generated each run.
        self.stdout.write('Clearing existing data...')
        try:
            from core.models import EmergencyRequest
            EmergencyRequest.objects.all().delete()
        except Exception:
            pass
        Ambulance.objects.all().delete()
        Hospital.objects.all().delete()
        Edge.objects.all().delete()
        Node.objects.all().delete()

        # ── MINI-CITY LAYOUT (irregular, non-grid) ──────────────
        BASE_LAT = 33.610
        BASE_LON = 73.020
        CITY_RADIUS = 0.055
        RINGS = 5
        SPOKES = 14

        self.stdout.write('Creating mini-city intersections...')

        all_nodes = []
        # City center / CBD
        center = Node.objects.create(label='CBD_0', latitude=BASE_LAT, longitude=BASE_LON)
        all_nodes.append(center)

        # Concentric rings with angle and radius jitter (looks like real city blocks)
        for ring in range(1, RINGS + 1):
            ring_ratio = ring / RINGS
            base_r = CITY_RADIUS * ring_ratio
            for spoke in range(SPOKES):
                # Small variation in angle and distance prevents a perfect geometric graph
                angle = (2 * math.pi * spoke / SPOKES) + random.uniform(-0.08, 0.08)
                r = base_r + random.uniform(-0.004, 0.004)
                lat = BASE_LAT + r * math.sin(angle)
                lon = BASE_LON + r * math.cos(angle) * 0.88  # lon compression for local projection feel
                label = f'R{ring}_S{spoke}'
                n = Node.objects.create(label=label, latitude=round(lat, 6), longitude=round(lon, 6))
                all_nodes.append(n)

        self.stdout.write(f'Created {len(all_nodes)} nodes')

        self.stdout.write('Creating road edges...')

        def dist_km(n1, n2):
            """Euclidean distance in km between two nodes."""
            lat1, lon1 = n1.latitude, n1.longitude
            lat2, lon2 = n2.latitude, n2.longitude
            dlat = (lat2 - lat1) * 111.0
            dlon = (lon2 - lon1) * 111.0 * math.cos(math.radians((lat1+lat2)/2))
            return round(math.sqrt(dlat**2 + dlon**2), 3)

        edge_count = 0
        created = set()

        def add_bidirectional(n1, n2, min_speed=28, max_speed=52, tw_min=0.8, tw_max=2.6):
            nonlocal edge_count
            if n1.id == n2.id:
                return
            key = tuple(sorted((n1.id, n2.id)))
            if key in created:
                return
            created.add(key)
            d = dist_km(n1, n2)
            speed = random.uniform(min_speed, max_speed)
            t = round(d / speed * 60, 2)
            traffic = round(random.uniform(tw_min, tw_max), 2)
            Edge.objects.create(source=n1, destination=n2, distance=d, travel_time=t, traffic_weight=traffic)
            Edge.objects.create(source=n2, destination=n1, distance=d, travel_time=t, traffic_weight=traffic)
            edge_count += 2

        # Helper maps for ring/spoke addressing
        ring_nodes = {ring: [] for ring in range(1, RINGS + 1)}
        for n in all_nodes:
            if n.label.startswith('R'):
                parts = n.label.split('_')
                ring_idx = int(parts[0][1:])
                ring_nodes[ring_idx].append(n)

        for ring in ring_nodes:
            ring_nodes[ring].sort(key=lambda x: int(x.label.split('_')[1][1:]))

        # 1) Ring roads
        for ring in range(1, RINGS + 1):
            nodes = ring_nodes[ring]
            n = len(nodes)
            for i in range(n):
                add_bidirectional(nodes[i], nodes[(i + 1) % n], min_speed=32, max_speed=50, tw_min=0.9, tw_max=2.1)

        # 2) Radial arterials from CBD outward
        for spoke in range(SPOKES):
            prev = center
            for ring in range(1, RINGS + 1):
                curr = ring_nodes[ring][spoke]
                add_bidirectional(prev, curr, min_speed=35, max_speed=58, tw_min=0.8, tw_max=1.9)
                prev = curr

        # 3) Irregular local connectors (mini-neighborhood streets)
        for ring in range(2, RINGS + 1):
            nodes = ring_nodes[ring]
            n = len(nodes)
            for i in range(n):
                if random.random() < 0.55:
                    add_bidirectional(nodes[i], nodes[(i + 2) % n], min_speed=24, max_speed=40, tw_min=1.0, tw_max=2.8)
                if random.random() < 0.30 and ring > 2:
                    add_bidirectional(nodes[i], ring_nodes[ring - 1][(i + 1) % n], min_speed=22, max_speed=38, tw_min=1.0, tw_max=3.0)

        self.stdout.write(f'   Created {edge_count} edges')

        # ── HOSPITALS ───────────────────────────────────────────
        self.stdout.write('Creating hospitals...')

        hospital_names = [
            "Holy Family Hospital",
            "Benazir Bhutto Hospital",
            "CMH Rawalpindi",
            "District Headquarters Hospital",
            "Services Hospital",
            "Shifa International",
            "Rawalpindi General Hospital",
            "Fauji Foundation Hospital",
        ]
        # Keep hospitals spread across outer and mid rings.
        hospital_nodes = ring_nodes[5][::2][:4] + ring_nodes[3][1::3][:4]
        for name, node in zip(hospital_names, hospital_nodes):
            Hospital.objects.create(name=name, node=node)
            self.stdout.write(f'   [OK] {name} at {node.label}')

        # ── AMBULANCES ──────────────────────────────────────────
        self.stdout.write('Creating ambulances...')

        ambulance_nodes = [center, ring_nodes[2][2], ring_nodes[2][6], ring_nodes[3][9], ring_nodes[4][12]]
        for i, node in enumerate(ambulance_nodes, 1):
            Ambulance.objects.create(name=f'Ambulance-{i:02d}', node=node, is_available=True)

        # ── SUMMARY ─────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(f'   Nodes:      {Node.objects.count()}')
        self.stdout.write(f'   Edges:      {Edge.objects.count()}')
        self.stdout.write(f'   Hospitals:  {Hospital.objects.count()}')
        self.stdout.write(f'   Ambulances: {Ambulance.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Now run:  python manage.py runserver')
