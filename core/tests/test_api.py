"""
API Tests for FastAPI Application
Contains all endpoint tests organized by feature
"""
import jwt
import pytest
from fastapi import status

from auth.jwt_cookie_auth import generate_access_token, generate_refresh_token
from tests.conftest import login_user
from core.config import settings


# ============================================================================
# ROOT ENDPOINT TESTS (/)
# ============================================================================
class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()


# ============================================================================
# AUTHENTICATION TESTS (Signup, Login, Logout, Refresh)
# ============================================================================
class TestAuthentication:
    """Tests for authentication endpoints"""
    
    def test_signup_success(self, client, test_user_credentials, db_session):
        """Test successful user signup with JWT cookies validation"""
        response = client.post("/signup", json=test_user_credentials)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "detail" in data
        assert "user" in data
        assert data["user"]["user_name"] == test_user_credentials["user_name"]
        
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_signup_duplicate_username(self, client, test_user):
        """Test signup with existing username fails"""
        response = client.post(
            "/signup",
            json={
                "user_name": test_user.user_name,
                "password": "somepassword"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_user):
        """Test successful user login with JWT cookies validation"""
        response = client.post(
            "/login",
            json={
                "user_name": test_user.user_name,
                "password": test_user.password
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "detail" in data
        assert "logged in" in data["detail"].lower()
        
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
        
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails"""
        response = client.post(
            "/login",
            json={
                "user_name": test_user.user_name,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails"""
        response = client.post(
            "/login",
            json={
                "user_name": "nonexistent",
                "password": "password"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_success(self, authenticated_client):
        """Test successful logout"""
        response = authenticated_client.post("/logout")
        assert response.status_code == status.HTTP_200_OK
        assert "logged out" in response.json()["detail"].lower()
    
    def test_logout_without_auth(self, client):
        """Test logout without authentication fails"""
        response = client.post("/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_tokens_success(self, authenticated_client):
        """Test successful token refresh"""
        response = authenticated_client.post("/refresh-tokens")
        assert response.status_code == status.HTTP_200_OK
        assert "refresh" in response.json()["detail"].lower()
        
        # Check new cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies
    
    def test_get_current_user(self, authenticated_client, test_user):
        """Test getting current authenticated user"""
        response = authenticated_client.get("/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["user_name"] == test_user.user_name
    
    def test_get_current_user_without_auth(self, client):
        """Test getting current user without authentication fails"""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

# ============================================================================
# COST CRUD TESTS
# ============================================================================
class TestCostCRUD:
    """Tests for cost CRUD operations"""
    
    def test_create_cost_success(self, authenticated_client, sample_cost_data):
        """Test successful cost creation"""
        response = authenticated_client.post("/costs", json=sample_cost_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == sample_cost_data["description"]
        assert data["amount"] == sample_cost_data["amount"]
        assert "id" in data
    
    def test_create_cost_without_auth(self, client, sample_cost_data):
        """Test cost creation without authentication fails"""
        response = client.post("/costs", json=sample_cost_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_cost_invalid_amount(self, authenticated_client):
        """Test cost creation with invalid amount fails"""
        response = authenticated_client.post(
            "/costs",
            json={
                "description": "Test",
                "amount": -10.0  # Negative amount
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_cost_missing_fields(self, authenticated_client):
        """Test cost creation with missing fields fails"""
        response = authenticated_client.post(
            "/costs",
            json={"description": "Test"}  # Missing amount
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_read_cost_success(self, authenticated_client, sample_cost_data):
        """Test successfully reading a cost"""
        # First create a cost
        create_response = authenticated_client.post("/costs", json=sample_cost_data)
        cost_id = create_response.json()["id"]
        
        # Then read it
        response = authenticated_client.get(f"/costs/{cost_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == cost_id
        assert data["description"] == sample_cost_data["description"]
    
    def test_read_nonexistent_cost(self, authenticated_client):
        """Test reading non-existent cost fails"""
        response = authenticated_client.get("/costs/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_read_cost_without_auth(self, client):
        """Test reading cost without authentication fails"""
        response = client.get("/costs/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_read_all_costs(self, authenticated_client, sample_cost_data):
        """Test reading all costs for authenticated user"""
        # Create multiple costs
        authenticated_client.post("/costs", json=sample_cost_data)
        authenticated_client.post(
            "/costs",
            json={
                "description": "Another expense",
                "amount": 50.25
            }
        )
        
        # Read all costs
        response = authenticated_client.get("/costs")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_read_all_costs_without_auth(self, client):
        """Test reading all costs without authentication fails"""
        response = client.get("/costs")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_cost_success(self, authenticated_client, sample_cost_data):
        """Test successfully updating a cost"""
        # Create a cost
        create_response = authenticated_client.post("/costs", json=sample_cost_data)
        cost_id = create_response.json()["id"]
        
        # Update it
        updated_data = {
            "description": "Updated expense",
            "amount": 200.75
        }
        response = authenticated_client.put(f"/costs/{cost_id}", json=updated_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == updated_data["description"]
        assert data["amount"] == updated_data["amount"]
    
    def test_update_cost_partial(self, authenticated_client, sample_cost_data):
        """Test partially updating a cost (only description)"""
        # Create a cost
        create_response = authenticated_client.post("/costs", json=sample_cost_data)
        cost_id = create_response.json()["id"]
        
        # Partial update
        response = authenticated_client.put(
            f"/costs/{cost_id}",
            json={"description": "Only description changed"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["description"] == "Only description changed"
        assert data["amount"] == sample_cost_data["amount"]  # Unchanged
    
    def test_update_nonexistent_cost(self, authenticated_client):
        """Test updating non-existent cost fails"""
        response = authenticated_client.put(
            "/costs/999999",
            json={"description": "Test", "amount": 100}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_cost_without_auth(self, client):
        """Test updating cost without authentication fails"""
        response = client.put(
            "/costs/1",
            json={"description": "Test"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_cost_success(self, authenticated_client, sample_cost_data):
        """Test successfully deleting a cost"""
        # Create a cost
        create_response = authenticated_client.post("/costs", json=sample_cost_data)
        cost_id = create_response.json()["id"]
        
        # Delete it
        response = authenticated_client.delete(f"/costs/{cost_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = authenticated_client.get(f"/costs/{cost_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_nonexistent_cost(self, authenticated_client):
        """Test deleting non-existent cost fails"""
        response = authenticated_client.delete("/costs/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_cost_without_auth(self, client):
        """Test deleting cost without authentication fails"""
        response = client.delete("/costs/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# AUTHORIZATION TESTS (User cannot access other users' costs)
# ============================================================================
class TestAuthorization:
    """Tests for authorization and access control"""
    
    def test_user_cannot_read_other_user_cost(self, client, db_session):
        """Test that a user cannot read another user's cost"""
        from models import UserModel, CostModel
        
        # Create two users
        user1 = UserModel(user_name="user1", password="pass1")
        user2 = UserModel(user_name="user2", password="pass2")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create a cost for user1
        cost = CostModel(
            user_id=user1.id,
            description="User1's cost",
            amount=100.0
        )
        db_session.add(cost)
        db_session.commit()
        db_session.refresh(cost)
        
        # Login as user2 using helper function
        login_response = login_user(client, "user2", "pass2")
        assert login_response.status_code == status.HTTP_200_OK
        
        # Try to read user1's cost
        response = client.get(f"/costs/{cost.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_user_cannot_update_other_user_cost(self, client, db_session):
        """Test that a user cannot update another user's cost"""
        from models import UserModel, CostModel
        
        # Create two users
        user1 = UserModel(user_name="user1", password="pass1")
        user2 = UserModel(user_name="user2", password="pass2")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create a cost for user1
        cost = CostModel(
            user_id=user1.id,
            description="User1's cost",
            amount=100.0
        )
        db_session.add(cost)
        db_session.commit()
        db_session.refresh(cost)
        
        # Login as user2 using helper function
        login_response = login_user(client, "user2", "pass2")
        assert login_response.status_code == status.HTTP_200_OK
        
        # Try to update user1's cost
        response = client.put(
            f"/costs/{cost.id}",
            json={"description": "Hacked"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_user_cannot_delete_other_user_cost(self, client, db_session):
        """Test that a user cannot delete another user's cost"""
        from models import UserModel, CostModel
        
        # Create two users
        user1 = UserModel(user_name="user1", password="pass1")
        user2 = UserModel(user_name="user2", password="pass2")
        db_session.add_all([user1, user2])
        db_session.commit()
        db_session.refresh(user1)
        db_session.refresh(user2)
        
        # Create a cost for user1
        cost = CostModel(
            user_id=user1.id,
            description="User1's cost",
            amount=100.0
        )
        db_session.add(cost)
        db_session.commit()
        db_session.refresh(cost)
        
        # Login as user2 using helper function
        login_response = login_user(client, "user2", "pass2")
        assert login_response.status_code == status.HTTP_200_OK
        
        # Try to delete user1's cost
        response = client.delete(f"/costs/{cost.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN






# # ============================================================================
# # JWT TOKEN VALIDATION TESTS
# # ============================================================================
# class TestJWTTokenValidation:
#     """Tests for JWT token validation and security"""
    
#     def test_access_with_invalid_token(self, client):
#         """Test that invalid JWT token is rejected"""
#         # Set invalid token in cookie
#         client.cookies.set("access_token", "invalid.jwt.token")
        
#         response = client.get("/auth/me")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
#     def test_access_with_wrong_token_type(self, client, test_user):
#         """Test that using refresh token as access token fails"""
#         # Use auth helper to generate refresh token
#         refresh_token = generate_refresh_token(test_user.id)
        
#         # Try to use refresh token as access token
#         client.cookies.clear()
#         client.cookies.set("access_token", refresh_token)
        
#         response = client.get("/auth/me")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#         assert "token type" in response.json()["detail"].lower()
    
#     def test_token_contains_user_id(self, client, test_user):
#         """Test that JWT tokens contain correct user_id using auth helpers"""
#         # Use auth helper to generate token
#         access_token = generate_access_token(test_user.id)
        
#         # Decode and verify
#         decoded = jwt.decode(
#             access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
#         )
        
#         assert decoded["user_id"] == test_user.id
    
#     def test_access_token_shorter_expiry_than_refresh(self, test_user):
#         """Test that access token expires before refresh token using auth helpers"""
#         # Use auth helpers to generate tokens
#         access_token = generate_access_token(test_user.id)
#         refresh_token = generate_refresh_token(test_user.id)
        
#         # Decode tokens
#         access_decoded = jwt.decode(
#             access_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
#         )
#         refresh_decoded = jwt.decode(
#             refresh_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
#         )
        
#         # Refresh token should expire later than access token
#         assert refresh_decoded["exp"] > access_decoded["exp"]
        
#         # Calculate expiry duration
#         access_duration = access_decoded["exp"] - access_decoded["iat"]
#         refresh_duration = refresh_decoded["exp"] - refresh_decoded["iat"]
        
#         # Access token: ~5 minutes (300 seconds)
#         # Refresh token: ~24 hours (86400 seconds)
#         assert access_duration < refresh_duration
#         assert access_duration == 300  # Exactly 5 minutes
#         assert refresh_duration == 86400  # Exactly 24 hours
    
#     def test_token_with_tampered_signature(self, client, test_user):
#         """Test that tokens with tampered signatures are rejected"""
#         # Use auth helper to generate valid token
#         access_token = generate_access_token(test_user.id)
        
#         # Tamper with the token by changing last character
#         tampered_token = access_token[:-5] + "XXXXX"
        
#         client.cookies.clear()
#         client.cookies.set("access_token", tampered_token)
        
#         response = client.get("/auth/me")
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
#     def test_logout_clears_cookies(self, authenticated_client):
#         """Test that logout clears authentication cookies"""
#         # Verify we're authenticated
#         me_response = authenticated_client.get("/auth/me")
#         assert me_response.status_code == status.HTTP_200_OK
        
#         # Logout
#         logout_response = authenticated_client.post("/logout")
#         assert logout_response.status_code == status.HTTP_200_OK
        
#         # Try to access protected endpoint after logout
#         # Note: TestClient doesn't automatically clear cookies on logout
#         # In real browser, cookies would be deleted