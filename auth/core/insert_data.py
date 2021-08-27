def insert_user_roles(target, connection, **kw):
    """Добавление ролей при создании таблицы"""
    base_roles = ("anonymous", "authenticated", "superuser", "subscriber")
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

    perm_subscriber = (*perm_auth, "can_watch_movies")

    permissions_subscriber = [
        {"role_id": role[0], "permission_id": permission[0]}
        for role in roles
        if role[1] == "subscriber"
        for permission in permissions
        if permission[1] in perm_subscriber
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
        *permissions_subscriber,
        *permissions_superuser
    )
