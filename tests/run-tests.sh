#!/bin/bash

restart_stack() {
    docker compose -f compose.testing.yaml down -v 2>/dev/null
    docker compose -f compose.testing.yaml up -d 2>/dev/null
    sleep 5
}

tests=(
    reload
    test_01_ping.tavern.yml
    test_02_business_signup.tavern.yml
    test_02_business_signup_invalid_password.tavern.yml
    reload
    test_03_business_signin.tavern.yml
    reload
    test_04_business_promo_create_valid.tavern.yml
    test_04_business_promo_create_valid_tricky.tavern.yml
    test_04_business_promo_create_invalid.tavern.yml
    reload
    test_04_business_promo_create_valid.tavern.yml
    test_05_business_promo_list.tavern.yml
    test_05_business_promo_list_invalid.tavern.yml
    reload
    test_06_business_promo_id_valid.tavern.yml
    test_06_business_promo_id_invalid.tavern.yml
    reload
    test_07_user_signup.tavern.yml
    test_07_user_signup_invalid.tavern.yml
    reload
    test_08_user_signin.tavern.yml
    reload
    test_09_user_profile.tavern.yml
    test_09_user_profile_invalid.tavern.yml
    reload
    test_10_user_feed.tavern.yml
    test_10_user_promo.tavern.yml
    reload
    test_11_user_like.tavern.yml
    reload
    test_12_user_comments.tavern.yml
    reload
    test_13_user_promo_activate.tavern.yml
    test_13_user_promo_activate_validate_cache.tavern.yml
    reload
    test_14_business_activate_promo.tavern.yml
    test_14_business_get_stat.tavern.yml
    reload
)

docker compose -f compose.testing.yaml up -d --build --force-recreate --remove-orphans 2>/dev/null

for test in "${tests[@]}"; do
    if [[ "$test" == "reload" ]]; then
        restart_stack
        continue
    fi

    uv run pytest "$test"
done

docker compose -f compose.testing.yaml down -v --remove-orphans 2>/dev/null
