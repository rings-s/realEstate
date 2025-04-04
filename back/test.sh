#!/bin/bash
# Complete API Testing Script for Real Estate Auction System
# Tests all endpoints defined in the URLs configuration

# Color codes for output formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL - adjust if your server is on a different port or host
BASE_URL="http://localhost:8000"

# API prefix - set to empty string if no prefix is used
API_PREFIX=""

# Login credentials
EMAIL="rings23@gmail.com"
PASSWORD="Africa123"

# IDs for testing detail endpoints
# Update these with actual IDs from your database
PROPERTY_ID="1"
AUCTION_ID="1"
BID_ID="1"
CONTRACT_ID="1"
PAYMENT_ID="1"
TRANSACTION_ID="1"
NOTIFICATION_ID="1"
THREAD_ID="1"
PROPERTY_VIEW_ID="1"

# Function to print section headers
print_header() {
  echo -e "\n${YELLOW}==================================================================${NC}"
  echo -e "${YELLOW}$1${NC}"
  echo -e "${YELLOW}==================================================================${NC}"
}

# Function to print subsection headers
print_subheader() {
  echo -e "\n${BLUE}------------------------------------------------------------------${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}------------------------------------------------------------------${NC}"
}

# Function to make API requests and check status code
make_request() {
  local method="$1"
  local endpoint="$2"
  local data="$3"
  local auth_header="$4"
  local expect_code="${5:-200}"
  
  echo -e "\n${YELLOW}Testing: $method $endpoint${NC}"
  
  # Create headers array
  headers=("-H" "Content-Type: application/json")
  
  # Add auth header if provided
  if [ ! -z "$auth_header" ]; then
    headers+=("-H" "Authorization: Bearer $auth_header")
  fi
  
  # Prepare data argument if provided
  data_arg=""
  if [ ! -z "$data" ]; then
    data_arg="-d '$data'"
  fi
  
  # Execute the curl command and save both status code and response body
  response=$(curl -s -w "\n%{http_code}" \
    -X "$method" \
    "${BASE_URL}${API_PREFIX}${endpoint}" \
    "${headers[@]}" \
    $data_arg)
  
  # Extract status code (last line) and response body (everything else)
  status_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  # Check if status code matches expected
  if [ "$status_code" -eq "$expect_code" ]; then
    echo -e "${GREEN}✓ Success! Status code: $status_code${NC}"
  else
    echo -e "${RED}✗ Failed! Expected status code $expect_code but got $status_code${NC}"
  fi
  
  # Print response body (with jq formatting if available)
  echo "$body" | jq 2>/dev/null || echo "$body"
  
  # Return the response body (without status code) for further processing
  echo "$body"
}

# Function to extract token from JSON response
extract_token() {
  local response="$1"
  local token_name="$2"
  
  # Try using jq if available
  if command -v jq &> /dev/null; then
    token=$(echo "$response" | jq -r ".$token_name" 2>/dev/null)
  else
    # Fallback to grep/sed
    token=$(echo "$response" | grep -o "\"$token_name\":\"[^\"]*\"" | sed "s/\"$token_name\":\"//;s/\"//")
  fi
  
  echo "$token"
}

# Main testing script starts here
print_header "REAL ESTATE AUCTION PLATFORM API TESTING"
echo -e "Testing environment: ${BASE_URL}${API_PREFIX}"
echo -e "Current date: $(date)"

print_header "Testing API connectivity"
make_request "GET" "/accounts/api/test/" "" ""

print_header "AUTHENTICATION ENDPOINTS"

# Login and get tokens
print_subheader "Login to obtain access tokens"
login_data="{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
login_response=$(make_request "POST" "/accounts/login/" "$login_data" "")

# Extract tokens from login response
ACCESS_TOKEN=$(extract_token "$login_response" "access")
REFRESH_TOKEN=$(extract_token "$login_response" "refresh")

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}Failed to get access token. Check your credentials.${NC}"
  echo -e "${YELLOW}Will continue with tests without authentication...${NC}"
  AUTH_HEADER=""
else
  echo -e "${GREEN}Got access token: $ACCESS_TOKEN${NC}"
  echo -e "${GREEN}Got refresh token: $REFRESH_TOKEN${NC}"
  AUTH_HEADER="$ACCESS_TOKEN"
  
  # Verify token
  print_subheader "Verifying token"
  make_request "POST" "/accounts/token/verify/" "{\"token\":\"$ACCESS_TOKEN\"}" "$AUTH_HEADER"
  
  # Refresh token
  print_subheader "Refreshing token"
  refresh_response=$(make_request "POST" "/accounts/token/refresh/" "{\"refresh\":\"$REFRESH_TOKEN\"}" "")
  
  # Extract new access token
  NEW_ACCESS_TOKEN=$(extract_token "$refresh_response" "access")
  if [ ! -z "$NEW_ACCESS_TOKEN" ]; then
    ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
    AUTH_HEADER="$ACCESS_TOKEN"
    echo -e "${GREEN}Updated access token: $ACCESS_TOKEN${NC}"
  fi
fi

print_header "USER PROFILE ENDPOINTS"
print_subheader "Get current user profile"
make_request "GET" "/accounts/profile/" "" "$AUTH_HEADER"

print_subheader "Update user profile"
profile_data='{
  "first_name": "Test",
  "last_name": "User",
  "phone_number": "+12345678901",
  "bio": "Test bio updated via API",
  "city": "Test City",
  "country": "Test Country"
}'
make_request "PUT" "/accounts/profile/" "$profile_data" "$AUTH_HEADER"

print_header "PROPERTY ENDPOINTS"
print_subheader "List properties"
make_request "GET" "/properties/" "" "$AUTH_HEADER"

print_subheader "Get user properties"
make_request "GET" "/properties/user-properties/" "" "$AUTH_HEADER"

print_subheader "Get recommended properties"
make_request "GET" "/properties/recommended/" "" "$AUTH_HEADER"

print_subheader "Get property by slug"
make_request "GET" "/properties/by-slug/test-property/" "" "$AUTH_HEADER"

print_subheader "Get property analytics"
make_request "GET" "/properties/analytics/" "" "$AUTH_HEADER"

print_subheader "Create property"
property_data='{
  "title": "Test Property",
  "property_type": "apartment",
  "description": "A test property created via API",
  "address": "123 Test St",
  "city": "Test City",
  "district": "Test District",
  "country": "Test Country",
  "area": 100,
  "estimated_value": 200000,
  "bedrooms": 2,
  "bathrooms": 1
}'
make_request "POST" "/properties/" "$property_data" "$AUTH_HEADER" "201"

print_subheader "Publish property"
make_request "POST" "/properties/${PROPERTY_ID}/publish/" "{}" "$AUTH_HEADER"

print_subheader "Unpublish property"
make_request "POST" "/properties/${PROPERTY_ID}/unpublish/" "{}" "$AUTH_HEADER"

print_subheader "Appraise property"
appraisal_data='{
  "estimated_value": 250000,
  "appraisal_notes": "Property value increased due to neighborhood development"
}'
make_request "POST" "/properties/${PROPERTY_ID}/appraise/" "$appraisal_data" "$AUTH_HEADER"

print_header "PROPERTY VIEW ENDPOINTS"
print_subheader "List property views"
make_request "GET" "/property-views/" "" "$AUTH_HEADER"

print_subheader "Get property views by auction"
make_request "GET" "/property-views/auction/${AUCTION_ID}/" "" "$AUTH_HEADER"

print_subheader "Update property view measurements"
measurement_data='{
  "size_sqm": 120.5,
  "elevation": 45
}'
make_request "POST" "/property-views/${PROPERTY_VIEW_ID}/update-measurements/" "$measurement_data" "$AUTH_HEADER"

print_subheader "Get property view analytics"
make_request "GET" "/property-views/analytics/" "" "$AUTH_HEADER"

print_header "AUCTION ENDPOINTS"
print_subheader "List auctions"
make_request "GET" "/auctions/" "" "$AUTH_HEADER"

print_subheader "Get user auctions"
make_request "GET" "/auctions/user-auctions/" "" "$AUTH_HEADER"

print_subheader "Get auction by slug"
make_request "GET" "/auctions/by-slug/test-auction/" "" "$AUTH_HEADER"

print_subheader "Get auction stats"
make_request "GET" "/auctions/${AUCTION_ID}/stats/" "" "$AUTH_HEADER"

print_subheader "Get auction analytics"
make_request "GET" "/auctions/analytics/" "" "$AUTH_HEADER"

print_subheader "Create auction"
auction_data='{
  "title": "Test Auction",
  "description": "A test auction created via API",
  "auction_type": "public", 
  "related_property": '${PROPERTY_ID}',
  "start_date": "2025-04-01T10:00:00Z",
  "end_date": "2025-04-10T10:00:00Z",
  "starting_price": 100000,
  "reserve_price": 120000,
  "min_bid_increment": 1000
}'
make_request "POST" "/auctions/" "$auction_data" "$AUTH_HEADER" "201"

print_subheader "Extend auction"
extend_data='{
  "minutes": 60
}'
make_request "POST" "/auctions/${AUCTION_ID}/extend/" "$extend_data" "$AUTH_HEADER"

print_subheader "Invite users to auction"
invite_data='{
  "user_ids": ["2", "3"],
  "emails": ["test@example.com"]
}'
make_request "POST" "/auctions/${AUCTION_ID}/invite/" "$invite_data" "$AUTH_HEADER"

print_subheader "Change auction status"
status_data='{
  "status": "closed"
}'
make_request "POST" "/auctions/${AUCTION_ID}/change-status/" "$status_data" "$AUTH_HEADER"

print_header "BID ENDPOINTS"
print_subheader "List bids"
make_request "GET" "/bids/" "" "$AUTH_HEADER"

print_subheader "Get user bids"
make_request "GET" "/bids/user-bids/" "" "$AUTH_HEADER"

print_subheader "Get bid analytics"
make_request "GET" "/bids/analytics/" "" "$AUTH_HEADER"

print_subheader "Get auction bid history"
make_request "GET" "/bids/auction-bid-history/?auction_id=${AUCTION_ID}" "" "$AUTH_HEADER"

print_subheader "Place bid"
bid_data='{
  "bid_amount": 105000
}'
make_request "POST" "/auctions/${AUCTION_ID}/bids/bid/" "$bid_data" "$AUTH_HEADER"

print_subheader "Mark bid as winning"
make_request "POST" "/bids/${BID_ID}/mark-winning/" "{}" "$AUTH_HEADER"

print_header "CONTRACT ENDPOINTS"
print_subheader "List contracts"
make_request "GET" "/contracts/" "" "$AUTH_HEADER"

print_subheader "Get user contracts"
make_request "GET" "/contracts/user-contracts/" "" "$AUTH_HEADER"

print_subheader "Get contract analytics"
make_request "GET" "/contracts/analytics/" "" "$AUTH_HEADER"

print_subheader "Get contract lifecycle data"
make_request "GET" "/contracts/contract-lifecycle/" "" "$AUTH_HEADER"

print_subheader "Sign contract"
sign_data='{
  "role": "buyer"
}'
make_request "POST" "/contracts/${CONTRACT_ID}/sign/" "$sign_data" "$AUTH_HEADER"

print_subheader "Update contract status"
contract_status_data='{
  "status": "active",
  "comments": "Contract activated after verification"
}'
make_request "POST" "/contracts/${CONTRACT_ID}/update-status/" "$contract_status_data" "$AUTH_HEADER"

print_subheader "Validate contract"
validate_data='{
  "notes": "Contract has been legally validated and is compliant with regulations"
}'
make_request "POST" "/contracts/${CONTRACT_ID}/validate/" "$validate_data" "$AUTH_HEADER"

print_header "PAYMENT ENDPOINTS"
print_subheader "List payments"
make_request "GET" "/payments/" "" "$AUTH_HEADER"

print_subheader "Get user payments"
make_request "GET" "/payments/user-payments/" "" "$AUTH_HEADER"

print_subheader "Get overdue payments"
make_request "GET" "/payments/overdue/" "" "$AUTH_HEADER"

print_subheader "Get payment analytics"
make_request "GET" "/payments/analytics/" "" "$AUTH_HEADER"

print_subheader "Get payment lifecycle data"
make_request "GET" "/payments/payment-lifecycle/" "" "$AUTH_HEADER"

print_subheader "Confirm payment"
confirm_data='{
  "notes": "Payment confirmed after bank verification"
}'
make_request "POST" "/payments/${PAYMENT_ID}/confirm/" "$confirm_data" "$AUTH_HEADER"

print_subheader "Reject payment"
reject_data='{
  "reason": "Payment rejected due to insufficient funds"
}'
make_request "POST" "/payments/${PAYMENT_ID}/reject/" "$reject_data" "$AUTH_HEADER"

print_header "TRANSACTION ENDPOINTS"
print_subheader "List transactions"
make_request "GET" "/transactions/" "" "$AUTH_HEADER"

print_subheader "Get user transactions"
make_request "GET" "/transactions/user-transactions/" "" "$AUTH_HEADER"

print_subheader "Get transaction summary"
make_request "GET" "/transactions/summary/" "" "$AUTH_HEADER"

print_subheader "Get transaction analytics"
make_request "GET" "/transactions/analytics/" "" "$AUTH_HEADER"

print_subheader "Get financial insights"
make_request "GET" "/transactions/financial-insights/" "" "$AUTH_HEADER"

print_subheader "Update transaction status"
transaction_status_data='{
  "status": "completed"
}'
make_request "POST" "/transactions/${TRANSACTION_ID}/update-status/" "$transaction_status_data" "$AUTH_HEADER"

print_header "MESSAGE THREAD ENDPOINTS"
print_subheader "List message threads"
make_request "GET" "/threads/" "" "$AUTH_HEADER"

print_subheader "Get user threads"
make_request "GET" "/threads/user-threads/" "" "$AUTH_HEADER"

print_subheader "Get thread analytics"
make_request "GET" "/threads/analytics/" "" "$AUTH_HEADER"

print_subheader "Get communication insights"
make_request "GET" "/threads/communication-insights/" "" "$AUTH_HEADER"

print_subheader "Get messages in thread"
make_request "GET" "/threads/${THREAD_ID}/messages/" "" "$AUTH_HEADER"

print_subheader "Send message to thread"
message_data='{
  "content": "This is a test message sent via API",
  "is_important": true
}'
make_request "POST" "/threads/${THREAD_ID}/send-message/" "$message_data" "$AUTH_HEADER"

print_subheader "Close thread"
make_request "POST" "/threads/${THREAD_ID}/close/" "{}" "$AUTH_HEADER"

print_subheader "Reopen thread"
make_request "POST" "/threads/${THREAD_ID}/reopen/" "{}" "$AUTH_HEADER"

print_subheader "Add participant to thread"
participant_data='{
  "user_id": "2",
  "role": "member"
}'
make_request "POST" "/threads/${THREAD_ID}/add-participant/" "$participant_data" "$AUTH_HEADER"

print_subheader "Leave thread"
make_request "POST" "/threads/${THREAD_ID}/leave/" "{}" "$AUTH_HEADER"

print_subheader "Toggle thread mute"
make_request "POST" "/threads/${THREAD_ID}/toggle-mute/" "{}" "$AUTH_HEADER"

print_header "NOTIFICATION ENDPOINTS"
print_subheader "List notifications"
make_request "GET" "/notifications/" "" "$AUTH_HEADER"

print_subheader "Get unread notification count"
make_request "GET" "/notifications/unread-count/" "" "$AUTH_HEADER"

print_subheader "Mark all notifications as read"
make_request "POST" "/notifications/mark-all-read/" "{}" "$AUTH_HEADER"

print_subheader "Mark specific notification as read"
make_request "POST" "/notifications/${NOTIFICATION_ID}/mark-as-read/" "{}" "$AUTH_HEADER"

print_subheader "Delete notification"
make_request "DELETE" "/notifications/${NOTIFICATION_ID}/delete/" "" "$AUTH_HEADER"

print_header "DASHBOARD ENDPOINT"
print_subheader "Get role-based dashboard"
make_request "GET" "/role_dashboard/" "" "$AUTH_HEADER"

# Logout user
if [ ! -z "$AUTH_HEADER" ]; then
  print_header "LOGOUT"
  make_request "POST" "/accounts/logout/" "{\"refresh\":\"$REFRESH_TOKEN\"}" "$AUTH_HEADER"
fi

print_header "API TESTING COMPLETE"
echo -e "${GREEN}Successfully tested $(grep -c "Testing:" "$0") endpoints${NC}"
echo -e "Testing completed at: $(date)"