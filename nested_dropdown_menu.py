import dash_bootstrap_components as dbc


def _options_to_dropdown_menu(menu_structure):
    '''
    Given a menu_structure (list of dictionaries)
    this function loops through it and generates (recursively) the expected dropdown menu using DropdownMenu and DropdownMenuItem objects
    '''
    children = []
    for element in menu_structure:
        if 'children' not in element:
            # simple element
            children.append(
                dbc.DropdownMenuItem(
                    element['label'],
                    href=element['href']
                )
            )
        else:
            # nested element
            nested_children = _options_to_dropdown_menu(  # recurse over children
                element['children']
            )
            children.append(
                dbc.DropdownMenu(
                    label=element['label'],
                    children=nested_children,
                    direction='right'
                )
            )
    return children


def nested_dropdown_menu(label, menu_structure):
    '''
    Given a label and a menu_structure, this function generates a menu and returns its root DropdownMenu component
    '''
    return dbc.DropdownMenu(
        label=label,
        className='dropdown_root',
        children=_options_to_dropdown_menu(menu_structure)
    )