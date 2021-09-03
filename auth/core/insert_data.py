def insert_user_roles(target, connection, **kw):
    """Добавление ролей при создании таблицы"""
    base_roles = (
        "anonymous",
        "authenticated",
        "superuser",
        "subscriber_bronze",
        "subscriber_silver",
        "subscriber_gold",
    )
    roles = [{"title": role} for role in base_roles]
    connection.execute(target.insert(), *roles)


def insert_permissions(target, connection, **kw):
    """Добавление правил при создании таблицы"""
    base_permissions = (
        "movies_get_film",
        "movies_get_film_list",
        "movies_get_genre",
        "movies_get_genre_list",
        "movies_get_person",
        "movies_get_person_list",
        "movies_search_film",
        "movies_search_person",
        "movies_create_film",
        "movies_change_film",
        "movies_delete_film",
        "movies_create_genre",
        "movies_change_genre",
        "movies_delete_genre",
        "movies_create_person",
        "movies_change_person",
        "movies_delete_person",
        "can_watch_movies",
    )
    permissions = [{"title": perm} for perm in base_permissions]
    connection.execute(target.insert(), *permissions)


def insert_user_role_permissions(target, connection, **kw):
    """Добавление правил в роли при создании таблицы"""
    roles = connection.execute("""SELECT * from role""")
    permissions = connection.execute("""SELECT * from permission""")
    roles = roles.fetchall()
    permissions = permissions.fetchall()

    perm_anonymous = (
        "movies_get_film",
        "movies_get_film_list",
        "movies_get_genre",
        "movies_get_genre_list",
        "movies_get_person",
        "movies_get_person_list",
    )

    permissions_anonymous = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "anonymous"
        for permission in permissions
        if permission[1] in perm_anonymous
    ]

    perm_auth = (*perm_anonymous, "movies_search_film", "movies_search_person")

    permissions_auth = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "authenticated"
        for permission in permissions
        if permission[1] in perm_auth
    ]

    perm_subscriber_bronze = (*perm_auth, "can_watch_movies", "quality_lower_HD")
    perm_subscriber_silver = (*perm_subscriber_bronze, "quality_HD")
    perm_subscriber_gold = (
        *perm_subscriber_silver,
        "can_watch_movies",
        "quality_lower_HD",
        "quality_higher_HD",
    )

    permissions_subscriber_bronze = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "subscriber_bronze"
        for permission in permissions
        if permission[1] in perm_subscriber_bronze
    ]

    permissions_subscriber_silver = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "subscriber_silver"
        for permission in permissions
        if permission[1] in perm_subscriber_silver
    ]

    permissions_subscriber_gold = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "subscriber_gold"
        for permission in permissions
        if permission[1] in perm_subscriber_gold
    ]

    perm_superuser = (
        *perm_auth,
        "movies_create_film",
        "movies_change_film",
        "movies_delete_film",
        "movies_create_genre",
        "movies_change_genre",
        "movies_delete_genre",
        "movies_create_person",
        "movies_change_person",
        "movies_delete_person",
    )

    permissions_superuser = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "superuser"
        for permission in permissions
        if permission[1] in perm_superuser
    ]

    connection.execute(
        target.insert(),
        *permissions_anonymous,
        *permissions_auth,
        *permissions_subscriber_bronze,
        *permissions_subscriber_silver,
        *permissions_subscriber_gold,
        *permissions_superuser
    )
