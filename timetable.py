import random
import mysql.connector

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="toor",
    database="xyz"
)

cursor = db.cursor(dictionary=True)


# Fetch subjects and teachers from the database
def fetch_subjects_and_teachers():
    query = """
    SELECT 
        sa.course_subject_id, 
        cs.subject_code, cs.subject_name, cs.year, cs.semester, cs.batch_id, cs.course_id, cs.is_active, cs.created_at,
        td.first_name, td.last_name, td.email, td.phone, td.department, td.appointment_date, td.photo_path
    FROM subject_assignments sa
    JOIN course_subjects cs ON sa.course_subject_id = cs.id
    JOIN teacher_details td ON sa.teacher_id = td.id
    WHERE cs.is_active = 1
    """
    cursor.execute(query)
    result = cursor.fetchall()

    subjects = {}
    for row in result:
        subject_name = row['subject_name']
        teacher_name = f"{row['first_name']} {row['last_name']}"
        batch_name = f"{row['year']}, {row['semester']}, {row['batch_id']}"
        subject_code = row['subject_code']
        teacher_details = {
            "name": teacher_name,
            "email": row['email'],
            "phone": row['phone'],
            "department": row['department'],
            "appointment_date": row['appointment_date'],
            "photo_path": row['photo_path']
        }

        if batch_name not in subjects:
            subjects[batch_name] = {}

        if subject_name not in subjects[batch_name]:
            # Assign random constraints for each subject
            max_periods_per_day = random.randint(1, 3)  # Random between 1-3 periods per day
            max_periods_per_week = random.randint(3, 8)  # Random between 3-8 periods per week

            subjects[batch_name][subject_name] = {
                "subject_code": subject_code,
                "teachers": [],
                "details": {
                    "course_id": row['course_id'],
                    "created_at": row['created_at']
                },
                "constraints": {
                    "max_periods_per_day": max_periods_per_day,
                    "max_periods_per_week": max_periods_per_week
                }
            }

        subjects[batch_name][subject_name]["teachers"].append(teacher_details)

    return subjects


# Timetable configuration
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
periods_per_day = 7
population_size = 10
generations = 100
mutation_rate = 0.1

# Fetch subjects and teachers
subjects = fetch_subjects_and_teachers()
batches = list(subjects.keys())


# Print subject constraints for verification
def print_subject_constraints():
    print("\n📋 Subject Constraints:")
    for batch in batches:
        print(f"\nBatch: {batch}")
        for subject, details in subjects[batch].items():
            max_day = details["constraints"]["max_periods_per_day"]
            max_week = details["constraints"]["max_periods_per_week"]
            print(f"  - {subject}: Max {max_day} per day, Max {max_week} per week")


# Generate initial population
def generate_initial_population():
    population = []
    for _ in range(population_size):
        timetable = {batch: {day: [""] * periods_per_day for day in days} for batch in batches}
        for batch in batches:
            for day in days:
                for period in range(periods_per_day):
                    subject = random.choice(list(subjects[batch].keys()))
                    teacher = random.choice(subjects[batch][subject]["teachers"])["name"]
                    timetable[batch][day][period] = f"{subject} ({teacher})"
        population.append(timetable)
    return population


# Fitness function
def fitness(timetable):
    penalty = 0
    teacher_schedule = {teacher["name"]: {day: [""] * periods_per_day for day in days} for batch in subjects for sub in
                        subjects[batch] for teacher in subjects[batch][sub]["teachers"]}

    for batch in batches:
        subject_weekly_count = {sub: 0 for sub in subjects[batch]}  # Track weekly count
        for day in days:
            daily_subject_count = {sub: 0 for sub in subjects[batch]}
            for period in range(periods_per_day):
                entry = timetable[batch][day][period]
                if entry:
                    subject, teacher = entry.rsplit(" (", 1)
                    teacher = teacher.rstrip(")")

                    # Get subject-specific constraints
                    max_periods_per_day = subjects[batch][subject]["constraints"]["max_periods_per_day"]
                    max_periods_per_week = subjects[batch][subject]["constraints"]["max_periods_per_week"]

                    # Enforce max periods per day
                    daily_subject_count[subject] += 1
                    if daily_subject_count[subject] > max_periods_per_day:
                        penalty += 3  # Penalty for exceeding max per day

                    # Track weekly count
                    subject_weekly_count[subject] += 1
                    if subject_weekly_count[subject] > max_periods_per_week:
                        penalty += 5  # Penalty for exceeding max per week

                    # Conflict check: No teacher overlap
                    if teacher_schedule[teacher][day][period] != "":
                        penalty += 5  # Penalty for teacher conflict
                    else:
                        teacher_schedule[teacher][day][period] = batch

    return penalty


# Selection function
def selection(population):
    sorted_population = sorted(population, key=lambda x: fitness(x))
    return sorted_population[:2]


# Crossover function
def crossover(parent1, parent2):
    child = {batch: {day: [""] * periods_per_day for day in days} for batch in batches}
    for batch in batches:
        for day in days:
            for period in range(periods_per_day):
                child[batch][day][period] = parent1[batch][day][period] if random.random() < 0.5 else \
                    parent2[batch][day][period]
    return child


# Mutation function
def mutate(timetable):
    for batch in batches:
        for day in days:
            if random.random() < mutation_rate:
                period = random.randint(0, periods_per_day - 1)
                subject = random.choice(list(subjects[batch].keys()))
                teacher = random.choice(subjects[batch][subject]["teachers"])["name"]
                timetable[batch][day][period] = f"{subject} ({teacher})"
    return timetable


# Main GA function
def create_timetable():
    print_subject_constraints()  # Print the generated constraints for verification

    population = generate_initial_population()
    best_fitness = float('inf')
    best_timetable = None

    for generation in range(1, generations + 1):
        new_population = []
        for _ in range(population_size):
            parent1, parent2 = selection(population)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population
        current_best = min(population, key=lambda x: fitness(x))
        current_fitness = fitness(current_best)

        if current_fitness < best_fitness:
            best_fitness = current_fitness
            best_timetable = current_best

        print(f"Generation {generation}: Best Fitness = {best_fitness}")

        if best_fitness <= 0:
            break

    return best_timetable


# Generate the timetable
final_timetable = create_timetable()

# Display the final timetable
for batch in batches:
    print(f"\n📅 Timetable for {batch}:")
    for day in days:
        print(f"{day}: {final_timetable[batch][day]}")


# Additional analysis of final timetable
def analyze_timetable(timetable):
    print("\n📊 Timetable Analysis:")

    for batch in batches:
        print(f"\nBatch: {batch}")
        subject_counts = {subject: {"daily": {day: 0 for day in days}, "total": 0}
                          for subject in subjects[batch]}

        for day in days:
            for period in range(periods_per_day):
                entry = timetable[batch][day][period]
                if entry:
                    subject, _ = entry.rsplit(" (", 1)
                    subject_counts[subject]["daily"][day] += 1
                    subject_counts[subject]["total"] += 1

        for subject, counts in subject_counts.items():
            constraints = subjects[batch][subject]["constraints"]
            print(f"  - {subject}:")
            print(f"    * Weekly total: {counts['total']} (max: {constraints['max_periods_per_week']})")
            for day in days:
                daily_count = counts["daily"][day]
                max_daily = constraints["max_periods_per_day"]
                status = "✅" if daily_count <= max_daily else "❌"
                print(f"    * {day}: {daily_count} periods {status}")


# Run analysis on the final timetable
analyze_timetable(final_timetable)