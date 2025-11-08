# Nginx for Docker Compose Production Deployment

This folder contains the Nginx configuration used to reverse-proxy services in a production Docker Compose setup, including:

- FastAPI backend
- Gradio interface
- Keycloak authentication server

---

## Notes

- Use this configuration with Docker Compose for production deployments.
- SSL certificates and security settings should be managed in the `conf.d` folder (e.g., `default.conf`) or mounted separately.
- Ensure all services are reachable by Nginx within the Docker network.

---
