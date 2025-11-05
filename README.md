Step 1- create a Docker network
docker network create llm-net

Step 2- Bring Keycloak up
cd keycloak
docker compose up -d

step 3. bring app up
cd ..
docker compose up -d


docker-compose --env-file .env up --build
Then:
	•	FastAPI API → http://localhost:8000
	•	Gradio UI → http://localhost:7860
	•	Keycloak → http://localhost:8080