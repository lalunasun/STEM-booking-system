TRIAL_PACKAGE_TEMPLATES = {
    'standard': {
        'key': 'standard',
        'label': 'Standard Robotics + Coding',
        'sessions': [
            {
                'label': 'Robotics',
                'subject': 'Robotics',
                'duration': 90,
                'subject_locked': False,
            },
            {
                'label': 'Coding',
                'subject': 'Coding',
                'duration': 90,
                'subject_locked': False,
            },
        ],
    },
    'creator': {
        'key': 'creator',
        'label': 'Creator Trial - 3 x 60 minutes',
        'sessions': [
            {
                'label': f'Creator {index}',
                'subject': 'Robotics',
                'course': 'Creator',
                'duration': 60,
                'start_interval': 60,
                'subject_locked': True,
            }
            for index in range(1, 4)
        ],
    },
    'creator_2x90': {
        'key': 'creator_2x90',
        'label': 'Creator Trial - 2 x 90 minutes',
        'sessions': [
            {
                'label': f'Creator {index}',
                'subject': 'Robotics',
                'course': 'Creator',
                'duration': 90,
                'subject_locked': True,
            }
            for index in range(1, 3)
        ],
    },
    'vex_v5': {
        'key': 'vex_v5',
        'label': 'VEX V5 Trial - 120 minutes + Coding',
        'sessions': [
            {
                'label': 'VEX V5',
                'subject': 'VEX V5',
                'course': 'VEX V5',
                'duration': 120,
                'subject_locked': True,
            },
            {
                'label': 'Coding',
                'subject': 'Coding',
                'duration': 60,
                'subject_locked': True,
            },
        ],
    },
}


def public_trial_package_templates():
    return [
        {
            'key': template['key'],
            'label': template['label'],
            'sessions': [dict(session) for session in template['sessions']],
        }
        for template in TRIAL_PACKAGE_TEMPLATES.values()
    ]


def trial_package_label(package_type):
    template = TRIAL_PACKAGE_TEMPLATES.get(package_type)
    return template['label'] if template else 'Trial'


def infer_trial_package_type(session_signatures):
    normalized = [
        ((course or '').strip().casefold(), int(duration))
        for course, duration in session_signatures
    ]
    if len(normalized) == 3 and all(
        course == 'creator' and duration == 60
        for course, duration in normalized
    ):
        return 'creator'
    if len(normalized) == 2 and all(
        course == 'creator' and duration == 90
        for course, duration in normalized
    ):
        return 'creator_2x90'
    if (
        len(normalized) == 2
        and normalized[0] == ('vex v5', 120)
        and normalized[1][1] == 60
    ):
        return 'vex_v5'
    return 'standard'
