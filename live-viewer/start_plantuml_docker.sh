#!/bin/bash


# Variables for the PlantUML Pico Server container
PLANTUML_IMAGE_NAME="plantuml/plantuml-server:jetty"
PLANTUML_CONTAINER_NAME="plantuml-server"
PLANTUML_PORT=8080


# Function to stop and remove a container
cleanup_container() {
  local container_name=$1
  local running_container=$(docker ps -q -f name=$container_name)

  if [ "$running_container" ]; then
    echo "Stopping container: $container_name..."
    docker stop $container_name
  fi

  local existing_container=$(docker ps -aq -f name=$container_name)

  if [ "$existing_container" ]; then
    echo "Removing container: $container_name..."
    docker rm $container_name
  fi
}


# Run the PlantUML Pico Server container
echo "Setting up the PlantUML Pico Server container..."
cleanup_container $PLANTUML_CONTAINER_NAME
docker run -d --name $PLANTUML_CONTAINER_NAME -p $PLANTUML_PORT:$PLANTUML_PORT $PLANTUML_IMAGE_NAME

if [ $? -ne 0 ]; then
  echo "Failed to start the PlantUML Pico Server container. Exiting."
  exit 1
fi

echo "PlantUML Pico Server is running:"
echo "  - URL: http://localhost:$PLANTUML_PORT"
