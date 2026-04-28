-- Required new objects: add_phone, move_to_group, search_contacts.

DROP PROCEDURE IF EXISTS add_phone(VARCHAR, VARCHAR, VARCHAR);
DROP PROCEDURE IF EXISTS move_to_group(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS search_contacts(TEXT);
DROP FUNCTION IF EXISTS get_contacts_paginated(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS show_all_contacts();
DROP FUNCTION IF EXISTS search_contacts_pattern(VARCHAR);
DROP FUNCTION IF EXISTS upsert_contact(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS bulk_insert_contacts(TEXT[], TEXT[]);
DROP FUNCTION IF EXISTS delete_contacts(VARCHAR, VARCHAR);

CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone VARCHAR,
    p_type VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_type VARCHAR(10);
BEGIN
    IF p_contact_name IS NULL OR BTRIM(p_contact_name) = '' THEN
        RAISE EXCEPTION 'Имя контакта не может быть пустым';
    END IF;

    IF p_phone IS NULL OR BTRIM(p_phone) = '' THEN
        RAISE EXCEPTION 'Телефон не может быть пустым';
    END IF;

    v_type := LOWER(COALESCE(NULLIF(BTRIM(p_type), ''), 'mobile'));
    IF v_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Тип телефона должен быть home, work или mobile';
    END IF;

    SELECT c.id INTO v_contact_id
    FROM contacts c
    WHERE LOWER(c.name) = LOWER(BTRIM(p_contact_name))
    ORDER BY c.id
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Контакт "%" не найден', p_contact_name;
    END IF;

    INSERT INTO phones(contact_id, phone, type)
    VALUES (v_contact_id, BTRIM(p_phone), v_type)
    ON CONFLICT (contact_id, phone) DO UPDATE
    SET type = EXCLUDED.type;

    UPDATE contacts
    SET phone = COALESCE(NULLIF(phone, ''), BTRIM(p_phone))
    WHERE id = v_contact_id;
END;
$$;

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id INTEGER;
    v_group_name VARCHAR(50);
BEGIN
    IF p_contact_name IS NULL OR BTRIM(p_contact_name) = '' THEN
        RAISE EXCEPTION 'Имя контакта не может быть пустым';
    END IF;

    v_group_name := COALESCE(NULLIF(BTRIM(p_group_name), ''), 'Other');

    SELECT c.id INTO v_contact_id
    FROM contacts c
    WHERE LOWER(c.name) = LOWER(BTRIM(p_contact_name))
    ORDER BY c.id
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Контакт "%" не найден', p_contact_name;
    END IF;

    INSERT INTO groups(name)
    VALUES (v_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT g.id INTO v_group_id
    FROM groups g
    WHERE g.name = v_group_name
    LIMIT 1;

    UPDATE contacts
    SET group_id = v_group_id
    WHERE id = v_contact_id;
END;
$$;

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT,
    created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_query TEXT := COALESCE(BTRIM(p_query), '');
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name AS group_name,
        COALESCE(STRING_AGG(p.type || ': ' || p.phone, ', ' ORDER BY p.type, p.phone), '') AS phones,
        c.created_at
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE v_query = ''
       OR c.name ILIKE '%' || v_query || '%'
       OR COALESCE(c.email, '') ILIKE '%' || v_query || '%'
       OR COALESCE(g.name, '') ILIKE '%' || v_query || '%'
       OR EXISTS (
            SELECT 1
            FROM phones px
            WHERE px.contact_id = c.id
              AND px.phone ILIKE '%' || v_query || '%'
       )
    GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
    ORDER BY c.name;
END;
$$;

-- Compatibility with the Practice 8 pagination call. It now works with phones table.
CREATE OR REPLACE FUNCTION get_contacts_paginated(
    page_number INTEGER,
    page_size INTEGER
)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    phone VARCHAR,
    created_at TIMESTAMP,
    total_count BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_offset INTEGER := GREATEST(page_number, 1) - 1;
    v_size INTEGER := GREATEST(page_size, 1);
    v_total BIGINT;
BEGIN
    v_offset := v_offset * v_size;
    SELECT COUNT(*) INTO v_total FROM contacts;

    RETURN QUERY
    SELECT
        c.id,
        c.name,
        COALESCE(
            (SELECT p.phone FROM phones p WHERE p.contact_id = c.id ORDER BY p.type, p.phone LIMIT 1),
            c.phone
        )::VARCHAR AS phone,
        c.created_at,
        v_total AS total_count
    FROM contacts c
    ORDER BY c.name
    LIMIT v_size
    OFFSET v_offset;
END;
$$;

-- Backward-compatible wrappers for older menu/tests. They use the new schema internally.
CREATE OR REPLACE FUNCTION search_contacts_pattern(search_pattern VARCHAR)
RETURNS TABLE(id INTEGER, name VARCHAR, phone VARCHAR, created_at TIMESTAMP)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT sc.id, sc.name,
           COALESCE((SELECT p.phone FROM phones p WHERE p.contact_id = sc.id ORDER BY p.type, p.phone LIMIT 1), '')::VARCHAR,
           sc.created_at
    FROM search_contacts(search_pattern) sc;
END;
$$;

CREATE OR REPLACE FUNCTION upsert_contact(p_name VARCHAR, p_phone VARCHAR)
RETURNS VARCHAR
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
    v_message VARCHAR;
BEGIN
    IF p_name IS NULL OR BTRIM(p_name) = '' THEN
        RAISE EXCEPTION 'Имя не может быть пустым';
    END IF;
    IF p_phone IS NULL OR BTRIM(p_phone) = '' THEN
        RAISE EXCEPTION 'Телефон не может быть пустым';
    END IF;

    SELECT c.id INTO v_contact_id
    FROM contacts c
    WHERE LOWER(c.name) = LOWER(BTRIM(p_name))
       OR EXISTS (SELECT 1 FROM phones p WHERE p.contact_id = c.id AND p.phone = BTRIM(p_phone))
    ORDER BY c.id
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        INSERT INTO contacts(name, phone, group_id)
        VALUES (BTRIM(p_name), BTRIM(p_phone), (SELECT id FROM groups WHERE name = 'Other'))
        RETURNING id INTO v_contact_id;
        v_message := 'Контакт добавлен: ' || BTRIM(p_name) || ' (' || BTRIM(p_phone) || ')';
    ELSE
        UPDATE contacts
        SET name = BTRIM(p_name), phone = BTRIM(p_phone)
        WHERE id = v_contact_id;
        v_message := 'Контакт обновлен: ' || BTRIM(p_name) || ' (' || BTRIM(p_phone) || ')';
    END IF;

    INSERT INTO phones(contact_id, phone, type)
    VALUES (v_contact_id, BTRIM(p_phone), 'mobile')
    ON CONFLICT (contact_id, phone) DO UPDATE SET type = EXCLUDED.type;

    RETURN v_message;
END;
$$;

CREATE OR REPLACE FUNCTION bulk_insert_contacts(names TEXT[], phones TEXT[])
RETURNS TABLE(invalid_name TEXT, invalid_phone TEXT, error_message TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    i INTEGER;
BEGIN
    IF COALESCE(array_length(names, 1), 0) <> COALESCE(array_length(phones, 1), 0) THEN
        RAISE EXCEPTION 'Количество имен и телефонов не совпадает';
    END IF;

    CREATE TEMP TABLE IF NOT EXISTS invalid_data(name TEXT, phone TEXT, error TEXT) ON COMMIT DROP;
    TRUNCATE invalid_data;

    FOR i IN 1..COALESCE(array_length(names, 1), 0) LOOP
        IF names[i] IS NULL OR BTRIM(names[i]) = '' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Имя не может быть пустым');
        ELSIF phones[i] IS NULL OR BTRIM(phones[i]) = '' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон не может быть пустым');
        ELSIF phones[i] !~ '^[0-9]+$' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон должен содержать только цифры');
        ELSIF LENGTH(phones[i]) < 9 OR LENGTH(phones[i]) > 15 THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон должен быть от 9 до 15 цифр');
        ELSE
            BEGIN
                PERFORM upsert_contact(names[i]::VARCHAR, phones[i]::VARCHAR);
            EXCEPTION WHEN OTHERS THEN
                INSERT INTO invalid_data VALUES (names[i], phones[i], SQLERRM);
            END;
        END IF;
    END LOOP;

    RETURN QUERY SELECT d.name, d.phone, d.error FROM invalid_data d;
END;
$$;

CREATE OR REPLACE FUNCTION delete_contacts(delete_by VARCHAR, delete_value VARCHAR)
RETURNS TABLE(deleted_id INTEGER, deleted_name VARCHAR, deleted_phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    IF delete_by = 'name' THEN
        RETURN QUERY
        DELETE FROM contacts c
        WHERE c.name ILIKE '%' || delete_value || '%'
        RETURNING c.id, c.name, c.phone;
    ELSIF delete_by = 'phone' THEN
        RETURN QUERY
        DELETE FROM contacts c
        WHERE EXISTS (SELECT 1 FROM phones p WHERE p.contact_id = c.id AND p.phone = delete_value)
           OR c.phone = delete_value
        RETURNING c.id, c.name, c.phone;
    ELSE
        RAISE EXCEPTION 'Параметр delete_by должен быть "name" или "phone"';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION show_all_contacts()
RETURNS TABLE(id INTEGER, name VARCHAR, phone VARCHAR, created_at TIMESTAMP)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name,
           COALESCE((SELECT p.phone FROM phones p WHERE p.contact_id = c.id ORDER BY p.type, p.phone LIMIT 1), c.phone)::VARCHAR,
           c.created_at
    FROM contacts c
    ORDER BY c.name;
END;
$$;
