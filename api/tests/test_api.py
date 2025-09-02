import pytest
from fastapi.testclient import TestClient
import json


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    @pytest.mark.api
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert data["service"] == "EvalWise API"
    
    @pytest.mark.api
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "EvalWise" in data["message"]


class TestRunEndpoints:
    """Test evaluation run endpoints"""
    
    @pytest.mark.api
    def test_create_run_success(self, client: TestClient, auth_headers, sample_run_data):
        """Test successful run creation"""
        response = client.post("/runs", json=sample_run_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_run_data["name"]
        assert data["dataset_id"] == sample_run_data["dataset_id"]
        assert data["status"] == "created"
        assert "created_at" in data
    
    @pytest.mark.api
    def test_create_run_no_auth(self, client: TestClient, sample_run_data):
        """Test run creation without authentication"""
        response = client.post("/runs", json=sample_run_data)
        assert response.status_code == 401
        
        data = response.json()
        assert data["error"] is True
        assert "Authentication required" in data["message"]
    
    @pytest.mark.api
    def test_create_run_invalid_data(self, client: TestClient, auth_headers):
        """Test run creation with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "dataset_id": "not-a-uuid",  # Invalid UUID
            "model_config": {}  # Missing required fields
        }
        
        response = client.post("/runs", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
        
        data = response.json()
        assert data["error"] is True
        assert "Validation failed" in data["message"]
        assert "details" in data
    
    @pytest.mark.api
    def test_get_runs(self, client: TestClient, auth_headers):
        """Test getting list of runs"""
        response = client.get("/runs", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.api
    def test_get_runs_no_auth(self, client: TestClient):
        """Test getting runs without authentication"""
        response = client.get("/runs")
        assert response.status_code == 401
    
    @pytest.mark.api
    def test_get_run_by_id(self, client: TestClient, auth_headers, sample_run_data):
        """Test getting specific run by ID"""
        # First create a run
        create_response = client.post("/runs", json=sample_run_data, headers=auth_headers)
        assert create_response.status_code == 200
        run_id = create_response.json()["id"]
        
        # Then get it by ID
        response = client.get(f"/runs/{run_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == run_id
        assert data["name"] == sample_run_data["name"]
    
    @pytest.mark.api
    def test_get_run_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent run"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/runs/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"] is True
        assert "not found" in data["message"].lower()
    
    @pytest.mark.api
    def test_execute_run(self, client: TestClient, auth_headers, sample_run_data):
        """Test executing a run"""
        # First create a run
        create_response = client.post("/runs", json=sample_run_data, headers=auth_headers)
        assert create_response.status_code == 200
        run_id = create_response.json()["id"]
        
        # Then execute it
        response = client.post(f"/runs/{run_id}/execute", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "started"


class TestDatasetEndpoints:
    """Test dataset endpoints"""
    
    @pytest.mark.api
    def test_get_datasets(self, client: TestClient, auth_headers):
        """Test getting list of datasets"""
        response = client.get("/datasets", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.api
    def test_get_datasets_no_auth(self, client: TestClient):
        """Test getting datasets without authentication"""
        response = client.get("/datasets")
        assert response.status_code == 401
    
    @pytest.mark.api
    def test_create_dataset(self, client: TestClient, auth_headers, sample_dataset_data):
        """Test creating a dataset"""
        response = client.post("/datasets", json=sample_dataset_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_dataset_data["name"]
        assert data["description"] == sample_dataset_data["description"]
        assert "created_at" in data
    
    @pytest.mark.api
    def test_create_dataset_invalid_data(self, client: TestClient, auth_headers):
        """Test creating dataset with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "data": "not_a_list"  # Should be a list
        }
        
        response = client.post("/datasets", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error


class TestResultsEndpoints:
    """Test results endpoints"""
    
    @pytest.mark.api
    def test_get_results_no_auth(self, client: TestClient):
        """Test getting results without authentication"""
        fake_run_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/runs/{fake_run_id}/results")
        assert response.status_code == 401
    
    @pytest.mark.api
    def test_get_results_with_auth(self, client: TestClient, auth_headers):
        """Test getting results with authentication"""
        fake_run_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/runs/{fake_run_id}/results", headers=auth_headers)
        # Should return 404 for non-existent run, not 401
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling and middleware"""
    
    @pytest.mark.api
    def test_not_found_endpoint(self, client: TestClient):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data  # FastAPI default format
    
    @pytest.mark.api
    def test_method_not_allowed(self, client: TestClient):
        """Test 405 error handling"""
        response = client.put("/health")  # Health endpoint only supports GET
        assert response.status_code == 405
    
    @pytest.mark.api
    def test_validation_error_format(self, client: TestClient, auth_headers):
        """Test validation error response format"""
        invalid_data = {"invalid": "data"}
        response = client.post("/runs", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] is True
        assert "error_id" in data
        assert "timestamp" in data
        assert "message" in data
        assert "details" in data
        assert isinstance(data["details"], list)
    
    @pytest.mark.api
    def test_request_tracking(self, client: TestClient):
        """Test request tracking middleware"""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Response should include request tracking headers or have consistent structure
        data = response.json()
        assert "timestamp" in data  # Indicates request was tracked


class TestAuthentication:
    """Test authentication on protected endpoints"""
    
    @pytest.mark.auth
    @pytest.mark.api
    def test_jwt_authentication(self, client: TestClient, auth_headers):
        """Test JWT token authentication on protected endpoints"""
        response = client.get("/runs", headers=auth_headers)
        assert response.status_code == 200
    
    @pytest.mark.auth
    @pytest.mark.api
    def test_api_key_authentication(self, client: TestClient, api_key_headers):
        """Test API key authentication on protected endpoints"""
        response = client.get("/runs", headers=api_key_headers)
        assert response.status_code == 200
    
    @pytest.mark.auth
    @pytest.mark.api
    def test_mixed_auth_endpoints(self, client: TestClient, auth_headers, api_key_headers):
        """Test that endpoints accepting both JWT and API keys work correctly"""
        # Test with JWT
        jwt_response = client.get("/auth/me", headers=auth_headers)
        assert jwt_response.status_code == 200
        
        # Test with API key
        api_response = client.get("/auth/me", headers=api_key_headers)
        assert api_response.status_code == 200
        
        # Both should return same user data
        jwt_data = jwt_response.json()
        api_data = api_response.json()
        assert jwt_data["id"] == api_data["id"]
        assert jwt_data["username"] == api_data["username"]