-- Создаем отдельную схему для нашего контента чтобы не перемешалось с сущностями Django
CREATE SCHEMA IF NOT EXISTS content;
-- Жанры которые могут быть у кинопроизведений
CREATE TABLE IF NOT EXISTS content.genre
(
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  timestamp with time zone,
    updated_at  timestamp with time zone
);
-- Создание перечисления для выбора типа кинопроизведения DO $$ BEGIN
DO
$$
    BEGIN
        CREATE TYPE content.film_work_type AS ENUM ('serial', 'movie');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END
$$;
-- Убраны актеры жанры режиссеры и сценаристы так как они находятся в отношении m2m с этой таблицей
CREATE TABLE IF NOT EXISTS content.film_work
(
    id            TEXT PRIMARY KEY,
    title         TEXT                   NOT NULL,
    description   TEXT,
    creation_date DATE,
    certificate   TEXT,
    file_path     TEXT,
    rating        FLOAT,
    type          content.film_work_type not null,
    created_at    timestamp with time zone,
    updated_at    timestamp with time zone
);
-- Обобщение для актера режиссера и сценариста
CREATE TABLE IF NOT EXISTS content.person
(
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    birth_date DATE,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);
-- m2m таблица для связывания кинопроизведений с жанрами
CREATE TABLE IF NOT EXISTS content.genre_film_work
(
    id           TEXT PRIMARY KEY,
    film_work_id TEXT NOT NULL,
    genre_id     TEXT NOT NULL,
    created_at   timestamp with time zone,
    FOREIGN KEY (film_work_id) REFERENCES content.film_work (id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES content.genre (id) ON DELETE CASCADE
);
-- Обязательно проверяется уникальность жанра и кинопроизведения чтобы не появлялось дублей
CREATE UNIQUE INDEX IF NOT EXISTS film_work_genre ON content.genre_film_work (film_work_id, genre_id);
-- Создание перечисления для выбора типа роли человека DO $$ BEGIN
DO
$$
    BEGIN
        CREATE TYPE content.role_type AS ENUM ('writer', 'actor', 'director');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END
$$;
-- m2m таблица для связывания кинопроизведений с участниками
CREATE TABLE IF NOT EXISTS content.person_film_work
(
    id           TEXT PRIMARY KEY,
    film_work_id TEXT NOT NULL,
    person_id    TEXT NOT NULL,
    role         TEXT NOT NULL,
    created_at   timestamp with time zone,
    FOREIGN KEY (film_work_id) REFERENCES content.film_work (id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES content.person (id) ON DELETE CASCADE
);
-- Обязательно проверяется уникальность кинопроизведения человека и роли человека чтобы не появлялось дублей
CREATE UNIQUE INDEX IF NOT EXISTS film_work_person_role ON content.person_film_work (film_work_id, person_id, role);
-- Создается триггер который обновляет поле updated_at связанного film_work при изменении таблиц m2m
CREATE OR REPLACE FUNCTION content.set_update_time() RETURNS TRIGGER AS
$$
DECLARE
    film_id TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        film_id = NEW.film_work_id;
        UPDATE content.film_work
        SET updated_at = clock_timestamp()
        WHERE id = film_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        film_id = NEW.film_work_id;
        UPDATE content.film_work
        SET updated_at = clock_timestamp()
        WHERE id = film_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        film_id = OLD.film_work_id;
        UPDATE content.film_work
        SET updated_at = clock_timestamp()
        WHERE id = film_id;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;
-- Удаление тригера нужно что бы избежать ошибок повторного определения при повторном создании схемы
DROP TRIGGER IF EXISTS set_film_work_update_when_relation_with_person_deleted_or_added ON content.person_film_work;
-- Установка тригера для таблицы person_film_work
CREATE TRIGGER set_film_work_update_when_relation_with_person_deleted_or_added
    AFTER
        INSERT
        OR
        UPDATE
        OR DELETE
    ON content.person_film_work
    FOR EACH ROW
EXECUTE PROCEDURE content.set_update_time();
-- Удаление тригера нужно что бы избежать ошибок повторного определения при повторном создании схемы
DROP TRIGGER IF EXISTS set_film_work_update_when_relation_with_genre_deleted_or_added ON content.genre_film_work;
-- Установка тригера для таблицы genre_film_work
CREATE TRIGGER set_film_work_update_when_relation_with_genre_deleted_or_added
    AFTER
        INSERT
        OR
        UPDATE
        OR DELETE
    ON content.genre_film_work
    FOR EACH ROW
EXECUTE PROCEDURE content.set_update_time();

-- Создаем отдельную схему для нашего контента чтобы не перемешалось с сущностями Django
CREATE SCHEMA IF NOT EXISTS subscription;
-- Виды подписок
CREATE TABLE IF NOT EXISTS subscription.sub
(
    id     TEXT PRIMARY KEY,
    name   TEXT     NOT NULL,
    period INTERVAL NOT NULL,
    price  BIGINT   NOT NULL
);
-- Фильмы входящие в подписку m2m
CREATE TABLE IF NOT EXISTS subscription.sub_film_work
(
    id      TEXT PRIMARY KEY,
    film_id TEXT NOT NULL,
    sub_id  TEXT NOT NULL,
    CONSTRAINT sub_film_work_fk_film_work FOREIGN KEY (sub_id)
        REFERENCES subscription.sub (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT sub_film_work_fk_sub FOREIGN KEY (film_id)
        REFERENCES content.film_work (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
);
-- Создание перечисления для статуса оплаты подписки
DO
$$
    BEGIN
        CREATE TYPE subscription.order_type AS ENUM ('in_progress', 'paid');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END
$$;
-- Заказы подписок
CREATE TABLE IF NOT EXISTS subscription.order
(
    id             TEXT                    NOT NULL,
    user_id        TEXT                    NOT NULL,
    sub_id         TEXT                    NOT NULL,
    type           subscription.order_type NOT NULL,
    payment_method TEXT                    NOT NULL,
    CONSTRAINT orders_pkey PRIMARY KEY (id),
    CONSTRAINT sub_id_fk FOREIGN KEY (sub_id)
        REFERENCES subscription.sub (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
);