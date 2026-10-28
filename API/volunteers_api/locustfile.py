import random
import uuid
from datetime import datetime, timedelta
from locust import HttpUser, TaskSet, SequentialTaskSet, task, between
from faker import Faker

fake = Faker("ru_RU")


def register_and_login(client, role_id: int) -> tuple[str | None, int | None]:
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"loadtest_{role_id}_{unique_suffix}@example.com"
    password = "TestPassword123!"
    full_name = fake.name()

    reg_payload = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role_id": role_id
    }
    with client.post(
        "/api/auth/register",
        json=reg_payload,
        name="/api/auth/register [Setup]",
        catch_response=True
    ) as reg_resp:
        if reg_resp.status_code not in (200, 201):
            reg_resp.failure(f"Ошибка регистрации: {reg_resp.status_code} {reg_resp.text}")
            return None, None

    login_data = {
        "username": email,
        "password": password
    }
    with client.post(
        "/api/auth/login",
        data=login_data,
        name="/api/auth/login [Setup]",
        catch_response=True
    ) as login_resp:
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            return token, role_id
        else:
            login_resp.failure(f"Ошибка входа: {login_resp.status_code} {login_resp.text}")
            return None, None

class VolunteerBehavior(TaskSet):
    def on_start(self):
        self.token, _ = register_and_login(self.client, role_id=1)
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.available_event_ids = []
        self.applied_event_ids = set()

    @task(5)
    def get_all_events(self):
        with self.client.get(
            "/api/events/",
            headers=self.headers,
            name="GET /api/events/",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                events = resp.json()
                if isinstance(events, list):
                    self.available_event_ids = [
                        e["id"] for e in events if "id" in e
                    ]
                resp.success()
            else:
                resp.failure(f"Не удалось получить список событий: {resp.status_code}")

    @task(3)
    def get_locations_reference(self):
        self.client.get(
            "/api/references/locations",
            headers=self.headers,
            name="GET /api/references/locations"
        )

    @task(2)
    def get_my_user_info(self):
        if not self.token:
            return
        self.client.get(
            "/api/users/me",
            headers=self.headers,
            name="GET /api/users/me"
        )

    @task(2)
    def get_my_applications(self):
        if not self.token:
            return
        self.client.get(
            "/api/applications/me",
            headers=self.headers,
            name="GET /api/applications/me"
        )

    @task(1)
    def update_volunteer_profile(self):
        if not self.token:
            return
        profile_payload = {
            "phone": fake.phone_number()[:20],
            "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=45).isoformat(),
            "interests": fake.sentence(nb_words=8),
            "skills": random.sample(
                ["Первая помощь", "Координация", "Фотосъемка", "Логистика", "Перевод", "IT-поддержка"],
                k=random.randint(1, 3)
            )
        }
        self.client.put(
            "/api/users/me/profile",
            json=profile_payload,
            headers=self.headers,
            name="PUT /api/users/me/profile"
        )

    @task(2)
    def apply_for_event(self):
        if not self.token or not self.available_event_ids:
            return

        candidates = [eid for eid in self.available_event_ids if eid not in self.applied_event_ids]
        if not candidates:
            return

        target_event_id = random.choice(candidates)
        with self.client.post(
            "/api/applications/",
            json={"event_id": target_event_id},
            headers=self.headers,
            name="POST /api/applications/",
            catch_response=True
        ) as resp:
            if resp.status_code in (200, 201):
                self.applied_event_ids.add(target_event_id)
                resp.success()
            elif resp.status_code == 400:
                self.applied_event_ids.add(target_event_id)
                resp.success()
            else:
                resp.failure(f"Ошибка подачи заявки: {resp.status_code} {resp.text}")


class OrganizerWorkflow(SequentialTaskSet):
    def on_start(self):
        self.token, _ = register_and_login(self.client, role_id=2)
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.location_ids = [1]
        self.category_ids = [1]
        self.last_created_event_id = None

    @task
    def step1_fetch_locations(self):
        with self.client.get(
            "/api/references/locations",
            headers=self.headers,
            name="GET /api/references/locations",
            catch_response=True  
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    self.location_ids = [loc["id"] for loc in data if "id" in loc]
                resp.success()
            else:
                resp.failure(f"Ошибка загрузки локаций: {resp.status_code}")

    @task
    def step2_fetch_categories(self):
        with self.client.get(
            "/api/references/categories",
            headers=self.headers,
            name="GET /api/references/categories",
            catch_response=True
        ) as resp:
            if resp.status_code == 200 and isinstance(resp.json(), list) and resp.json():
                self.category_ids = [cat["id"] for cat in resp.json() if "id" in cat]
                resp.success()
            elif resp.status_code == 404:
                resp.success()

    @task
    def step3_create_event(self):
        if not self.token:
            return

        future_date = datetime.now() + timedelta(days=random.randint(5, 60))
        event_payload = {
            "title": f"Волонтерская акция «{fake.company()}» — {fake.city_name()}",
            "description": fake.text(max_nb_chars=180),
            "location_id": random.choice(self.location_ids) if self.location_ids else 1,
            "event_date": future_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "max_participants": random.randint(15, 100),
            "category_ids": [random.choice(self.category_ids)] if self.category_ids else [1]
        }

        with self.client.post(
            "/api/events/",
            json=event_payload,
            headers=self.headers,
            name="POST /api/events/",
            catch_response=True
        ) as resp:
            if resp.status_code in (200, 201):
                data = resp.json()
                self.last_created_event_id = data.get("id")
                resp.success()
            else:
                resp.failure(f"Ошибка создания события: {resp.status_code} {resp.text}")

    @task
    def step4_get_my_organized_events(self):
        if not self.token:
            return
        self.client.get(
            "/api/events/me",
            headers=self.headers,
            name="GET /api/events/me"
        )

    @task
    def step5_check_event_applications(self):
        if not self.token or not self.last_created_event_id:
            # Если мероприятие не было создано, запрашиваем профиль организатора
            self.client.get("/api/users/me", headers=self.headers, name="GET /api/users/me")
            return

        self.client.get(
            f"/api/events/{self.last_created_event_id}/applications",
            headers=self.headers,
            name="GET /api/events/{id}/applications"
        )

    @task
    def step6_verify_public_feed(self):
        self.client.get(
            "/api/events/",
            headers=self.headers,
            name="GET /api/events/"
        )

class VolunteerUser(HttpUser):
    tasks = [VolunteerBehavior]
    wait_time = between(1, 3)
    weight = 3


class OrganizerUser(HttpUser):
    tasks = [OrganizerWorkflow]
    wait_time = between(2, 4)
    weight = 1