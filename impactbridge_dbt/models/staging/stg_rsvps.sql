with source as (
    select * from {{ source('impactbridge', 'session_rsvps') }}
),

renamed as (
    select
        id              as rsvp_id,
        session_id,
        volunteer_id,
        status,
        case
            when status = 'confirmed' then 1
            else 0
        end             as confirmed_flag,
        responded_at
    from source
)

select * from renamed
