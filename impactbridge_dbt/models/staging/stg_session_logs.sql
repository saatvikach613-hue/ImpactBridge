with source as (
    select * from {{ source('impactbridge', 'session_logs') }}
),

renamed as (
    select
        id                  as log_id,
        kid_id,
        volunteer_id,
        session_id,
        subject,
        chapter_covered,
        rating,
        case
            when rating = 'struggling' then 1
            when rating = 'okay'       then 2
            when rating = 'nailed_it'  then 3
            else 2
        end                 as rating_num,
        notes,
        logged_at
    from source
    where logged_at is not null
)

select * from renamed
