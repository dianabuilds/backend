#!/usr/bin/env bash
# Basic HTTPie examples for workspace endpoints

# List workspaces
http GET :8000/admin/workspaces

# Create a workspace
http POST :8000/admin/workspaces/123e4567-e89b-12d3-a456-426614174000 name=Demo slug=demo

# List nodes in the workspace
http GET :8000/admin/workspaces/123e4567-e89b-12d3-a456-426614174000/nodes/all node_type==article
