# Introduction

Given that Hedgedoc doesn't support APIs to sync from GitHub up to v1.9.9, these tools rely on [GitHub REST API](https://docs.github.com/en/rest/repos) to retrieve and upload notes. Therefore, they only work for the notes synced via GitHub. Also, they only work for email login.

*git2hedge.py* fetches from GitHub to Hedgedoc by creating notes via Hedgedoc API **`/new`** and **`/history`**. The former is used to create a note in the database, and the latter is used to create an entry in the browsing history. This is essential because the Hedgedoc dashboard displays only browsing records up to v1.9.9. Each sync creates a log *note_sync_YYYYMMDD* as a record that can be used to sync back to GitHub. This log is important because it corresponds unstructured notes to possibly structured files on the Github repo. By structuring, for notes in the server, it can be done by creating book mode; for files on the Github repo, it can be achieved by creating subdirectories for different layers of book indexes.

Additionally, This tool depends on *credentials.json* which should include the following information.

```json 
{
  "github_owner": "Github repo owner",
  "github_repo": "Github repo used to sync Hackmd/Hedgedoc notes",
  "github_token": "Github token",
  "hedgedoc_email": "Hedgedoc user email",
  "hedgedoc_password": "Hedgedoc user password"
}
```

*hedge2git.py* fetches notes from the database directly due to the lack of functionality in both Hedgedoc API and [hedgedoc-cli](https://github.com/hedgedoc/cli/).

## Usage

The following shows all the available options and the default values.

### git2hedge

```bash 
python git2hedge
    --credential-file credentials.json
    --hedgedoc-server http://localhost/hedgedoc
```

* **`--hedgedoc-server`** specify the Hedgedoc server. You may want to set it to *http://hedgedoc-server:3000/*.

### hedge2git

```bash
TBC
```

# TODO

* Make all references to files as absolute path based on the python script.

## git2hedge

* Create book mode structures based on the GitHub structures.
    * Use tags to identify index.
    * Ignore files with index tag.
    * Use mustache for index templating.
* Support for LDAP login.

## hedge2git

* Create corresponding schema in *schema.py*.
* Add, commit and push all the files based on the latest log.
    * Make option for specifying a specific log.
* Create

## hedge-utils

* Clear all notes.
    * White list.