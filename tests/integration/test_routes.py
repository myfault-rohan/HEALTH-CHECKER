"""Integration tests for HTTP routes — tests the full request/response cycle."""

import pytest


class TestPublicPages:
    """Test pages accessible without login."""

    def test_landing_page(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Health Checker" in response.data

    def test_about_page(self, client):
        response = client.get("/about")
        assert response.status_code == 200

    def test_contact_page_get(self, client):
        response = client.get("/contact")
        assert response.status_code == 200

    def test_contact_form_empty_fields(self, client):
        response = client.post(
            "/contact",
            data={"name": "", "email": "", "message": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"complete all contact" in response.data.lower()

    def test_login_page(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Sign in" in response.data or b"sign in" in response.data

    def test_signup_page(self, client):
        response = client.get("/signup")
        assert response.status_code == 200


class TestAuth:
    """Test authentication flows."""

    def test_signup_success(self, client):
        response = client.post(
            "/signup",
            data={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Account created" in response.data or b"Dashboard" in response.data.title()

    def test_signup_short_password(self, client):
        response = client.post(
            "/signup",
            data={
                "email": "short@test.com",
                "password": "abc",
                "confirm_password": "abc",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"8 characters" in response.data

    def test_signup_mismatched_passwords(self, client):
        response = client.post(
            "/signup",
            data={
                "email": "mismatch@test.com",
                "password": "Password123!",
                "confirm_password": "Different123!",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data

    def test_signup_invalid_email(self, client):
        response = client.post(
            "/signup",
            data={
                "email": "not-an-email",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"valid email" in response.data

    def test_login_wrong_password(self, client):
        response = client.post(
            "/login",
            data={"email": "nobody@test.com", "password": "wrong"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data or b"invalid" in response.data

    def test_logout(self, authenticated_client):
        response = authenticated_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out" in response.data.lower()


class TestProtectedRoutes:
    """Test that protected routes redirect unauthenticated users."""

    @pytest.mark.parametrize(
        "path",
        ["/dashboard", "/info", "/symptoms", "/profile", "/start-over"],
    )
    def test_redirect_to_login(self, client, path):
        response = client.get(path)
        # Should redirect (302) to login
        assert response.status_code == 302
        assert "/login" in response.headers.get("Location", "")

    def test_api_returns_401(self, client):
        response = client.post(
            "/api/chat",
            json={"message": "I have a headache"},
            content_type="application/json",
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestCheckerFlow:
    """Test the core symptom-checker workflow end-to-end."""

    def test_info_page_loads(self, authenticated_client):
        response = authenticated_client.get("/info")
        assert response.status_code == 200
        assert b"age" in response.data.lower() or b"profile" in response.data.lower()

    def test_info_submit(self, authenticated_client):
        response = authenticated_client.post(
            "/info",
            data={"age": "25", "gender": "male"},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_info_invalid_age(self, authenticated_client):
        response = authenticated_client.post(
            "/info",
            data={"age": "0", "gender": "male"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"valid age" in response.data.lower()

    def test_symptoms_page_requires_profile(self, authenticated_client):
        # Without setting age/gender first, should redirect
        response = authenticated_client.get("/symptoms")
        # Could be 200 (with flash) or 302 (redirect to info)
        assert response.status_code in (200, 302)

    def test_full_check_flow(self, authenticated_client):
        """Test the complete flow: info → check → conditions."""
        # Step 1: Set profile
        authenticated_client.post(
            "/info",
            data={"age": "30", "gender": "male"},
            follow_redirects=True,
        )

        # Step 2: Submit symptoms
        response = authenticated_client.post(
            "/check",
            data={"symptoms": ["fever", "cough"]},
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_check_no_symptoms_redirects(self, authenticated_client):
        authenticated_client.post(
            "/info",
            data={"age": "30", "gender": "male"},
            follow_redirects=True,
        )
        response = authenticated_client.post(
            "/check",
            data={"symptoms": []},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"at least one" in response.data.lower()


@pytest.mark.integration
class TestDashboard:
    """Test dashboard routes."""

    def test_dashboard_loads(self, authenticated_client):
        response = authenticated_client.get("/dashboard")
        assert response.status_code == 200

    def test_history_stats_api(self, authenticated_client):
        response = authenticated_client.get("/api/history-stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "health_score" in data
        assert "total_checks" in data


@pytest.mark.integration
class TestProfile:
    """Test profile routes."""

    def test_profile_loads(self, authenticated_client):
        response = authenticated_client.get("/profile", follow_redirects=True)
        assert response.status_code == 200

    def test_csv_export(self, authenticated_client):
        # authenticated_client has a profile created on signup
        response = authenticated_client.get("/profile/export-csv", follow_redirects=True)
        assert response.status_code == 200


@pytest.mark.integration
class TestRBAC:
    """Test Role-Based Access Control and clinician privacy protections."""

    def test_doctor_dashboard_restricted_for_patient(self, authenticated_client):
        # authenticated_client is test@example.com (patient)
        response = authenticated_client.get("/doctor/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert b"Access denied" in response.data or b"Clinician" in response.data

    def test_doctor_dashboard_allowed_for_doctor(self, client):
        # Register a doctor account
        client.post(
            "/signup",
            data={
                "email": "doctor@clinic.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            },
            follow_redirects=True,
        )
        # Access doctor dashboard
        response = client.get("/doctor/dashboard")
        assert response.status_code == 200
        assert b"Doctor Portal" in response.data

    def test_bulk_export_restricted_for_patient(self, authenticated_client):
        response = authenticated_client.get("/api/research/export/bulk", follow_redirects=True)
        # Should redirect with warning or return 403
        assert response.status_code in (200, 403)
        assert b"Access denied" in response.data or b"Forbidden" in response.data

    def test_bulk_export_allowed_for_doctor(self, client):
        # Register doctor@clinic.com first to ensure test independence
        client.post(
            "/signup",
            data={
                "email": "doctor@clinic.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
            },
            follow_redirects=True,
        )
        # Login doctor@clinic.com
        client.post(
            "/login",
            data={
                "email": "doctor@clinic.com",
                "password": "SecurePass123!",
            },
            follow_redirects=True,
        )
        response = client.get("/api/research/export/bulk")
        assert response.status_code == 200
        data = response.get_json()
        assert "records" in data

