def row_to_dict(row):
    if row is None:
        return None

    return {
        key: row[key]
        for key in row.keys()
    }



