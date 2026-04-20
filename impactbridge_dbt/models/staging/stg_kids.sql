with source as (
    select * from {{ source('impactbridge', 'kids') }}
),

renamed as (
    select
        id              as kid_id,
        name            as kid_name,
        age,
        chapter_id,
        math_level      as current_math_level,
        english_level   as current_english_level,
        learning_style,
        interests,
        unlock_note,
        is_active
    from source
    where is_active = true
)

select * from renamed
