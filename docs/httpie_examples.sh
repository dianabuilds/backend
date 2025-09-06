#!/usr/bin/env bash
# Basic HTTPie examples for account endpoints

# List accounts (first page, 10 items)
http GET :8000/admin/accounts limit==10

# Create an account
http POST :8000/admin/accounts/123e4567-e89b-12d3-a456-426614174000 name=Demo slug=demo

# List nodes in the account
http GET :8000/admin/accounts/123e4567-e89b-12d3-a456-426614174000/nodes/all node_type==article
