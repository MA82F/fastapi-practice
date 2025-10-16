from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        response = self.client.post("/login", json={
                "user_name": "string",
                "password": "string"
        })

        # print("Login response text:", response.text)
        # print("Login error detail:", response.json())
        # print("Login status:", response.status_code)
        # print("Response headers:", response.headers)
        # print("Response cookies:", response.cookies.get_dict())
        # print("Session cookies after login:", self.client.cookies.get_dict())
        # ==========================
        # For Setting JWT in header:
        # ==========================

        # response = self.client.post("/users/login", json={
        #     "username": "string",
        #     "password": "string"
        # })
        # access_token = response.json()["access_token"]
        # self.client.headers = {'Authorization': f'Bearer {access_token}'}

    @task
    def route_test(self):
        self.client.get("/")

    @task
    def cost_create(self):
        self.client.post("/costs", json={
            "description": "string",
            "amount": 50
        })

    @task
    def refresh_tokens(self):
        self.client.post("/refresh-tokens")

    @task
    def costs_list(self):
        self.client.get("/costs")

    @task
    def not_found(self):
        self.client.get("/not-found")
