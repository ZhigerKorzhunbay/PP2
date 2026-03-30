CREATE OR REPLACE FUNCTION search_contacts_pattern(
    search_pattern VARCHAR
)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    phone VARCHAR,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.phone, c.created_at
    FROM contacts c
    WHERE 
        c.name ILIKE '%' || search_pattern || '%'
        OR c.phone ILIKE '%' || search_pattern || '%';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION upsert_contact(
    p_name VARCHAR,
    p_phone VARCHAR
)
RETURNS VARCHAR AS $$
DECLARE
    result_message VARCHAR;
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE phone = p_phone) THEN
        UPDATE contacts 
        SET name = p_name 
        WHERE phone = p_phone;
        result_message := 'Контакт обновлен: ' || p_name || ' (' || p_phone || ')';
    ELSE
        INSERT INTO contacts (name, phone) 
        VALUES (p_name, p_phone);
        result_message := 'Контакт добавлен: ' || p_name || ' (' || p_phone || ')';
    END IF;
    
    RETURN result_message;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION bulk_insert_contacts(
    names TEXT[],
    phones TEXT[]
)
RETURNS TABLE(
    invalid_name TEXT,
    invalid_phone TEXT,
    error_message TEXT
) AS $$
DECLARE
    i INTEGER;
    is_valid BOOLEAN;
BEGIN
    CREATE TEMP TABLE IF NOT EXISTS invalid_data (
        name TEXT,
        phone TEXT,
        error TEXT
    );
    
    DELETE FROM invalid_data;
    
    IF array_length(names, 1) != array_length(phones, 1) THEN
        RAISE EXCEPTION 'Количество имен и телефонов не совпадает';
    END IF;
    
    FOR i IN 1..array_length(names, 1) LOOP
        is_valid := TRUE;
        
        IF phones[i] IS NULL OR phones[i] = '' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон не может быть пустым');
            is_valid := FALSE;
        ELSIF phones[i] !~ '^[0-9]+$' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон должен содержать только цифры');
            is_valid := FALSE;
        ELSIF length(phones[i]) < 9 OR length(phones[i]) > 15 THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Телефон должен быть от 9 до 15 цифр');
            is_valid := FALSE;
        END IF;
        
        IF names[i] IS NULL OR names[i] = '' THEN
            INSERT INTO invalid_data VALUES (names[i], phones[i], 'Имя не может быть пустым');
            is_valid := FALSE;
        END IF;
        
        IF is_valid THEN
            BEGIN
                INSERT INTO contacts (name, phone) 
                VALUES (names[i], phones[i])
                ON CONFLICT (phone) DO UPDATE 
                SET name = EXCLUDED.name;
            EXCEPTION WHEN OTHERS THEN
                INSERT INTO invalid_data VALUES (names[i], phones[i], SQLERRM);
            END;
        END IF;
    END LOOP;
    
    RETURN QUERY
    SELECT id.name, id.phone, id.error
    FROM invalid_data id;
    
    DROP TABLE invalid_data;
END;
$$ LANGUAGE plpgsql;

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
) AS $$
DECLARE
    offset_val INTEGER;
    total BIGINT;
BEGIN
    offset_val := (page_number - 1) * page_size;
    
    SELECT COUNT(*) INTO total FROM contacts;
    
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        c.phone,
        c.created_at,
        total AS total_count
    FROM contacts c
    ORDER BY c.name
    LIMIT page_size
    OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_contacts(
    delete_by VARCHAR,
    delete_value VARCHAR
)
RETURNS TABLE(
    deleted_id INTEGER,
    deleted_name VARCHAR,
    deleted_phone VARCHAR
) AS $$
BEGIN
    IF delete_by = 'name' THEN
        RETURN QUERY
        DELETE FROM contacts
        WHERE name ILIKE '%' || delete_value || '%'
        RETURNING id, name, phone;
    ELSIF delete_by = 'phone' THEN
        RETURN QUERY
        DELETE FROM contacts
        WHERE phone = delete_value
        RETURNING id, name, phone;
    ELSE
        RAISE EXCEPTION 'Параметр delete_by должен быть "name" или "phone"';
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION show_all_contacts()
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    phone VARCHAR,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.phone, c.created_at
    FROM contacts c
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;