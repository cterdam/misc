"""Validate Google Form responses to prevent duplicate responses."""

from pathlib import Path
import sys
import zipfile

from loguru import logger
import pandas as pd
import yaml


def main():

    ###################################################################################
    # Logging

    logger.remove()
    logger.add(sys.stdout, format="<level>{message}</>")
    logger.level("INFO", color=logger.level("INFO").color.replace("<bold>", ""))

    ###################################################################################
    # Constants

    zip_csv_loc = Path("~/Downloads/Vote.csv.zip").expanduser()
    csv_name = "Vote.csv"
    voter_list_loc = Path("~/cterdam/misc/voters.yaml").expanduser()
    voter_col = "Voter ID"
    timestamp_col = "Timestamp"
    team_col = "I'm voting for"

    ###################################################################################

    # Read and proprocess CSV
    with zipfile.ZipFile(zip_csv_loc) as zip_csv_file:
        with zip_csv_file.open(csv_name) as csv_file:
            votes = pd.read_csv(csv_file)
    votes[voter_col] = votes[voter_col].str.upper()
    votes[timestamp_col] = pd.to_datetime(votes[timestamp_col]).dt.time

    logger.success(f"{len(votes)} VOTES LOADED")
    logger.info(votes)

    # Load valid voter IDs
    with open(voter_list_loc) as id_list_file:
        voter_list = yaml.safe_load(id_list_file)

    # filter out invalid IDs
    invalid_voters = ~votes[voter_col].isin(voter_list)
    invalid_votes = votes[invalid_voters]
    votes = votes[~invalid_voters]

    logger.error(f"{len(invalid_votes)} VOTES BY INVALID VOTERS")
    logger.info(invalid_votes)

    logger.success(f"{len(votes)} VOTES BY VALID VOTERS ")
    logger.info(votes)

    # Find voters with duplicate votes
    vote_counts = votes.groupby(voter_col).size().reset_index(name="Vote count")
    dup_voters = vote_counts[vote_counts["Vote count"] > 1]

    logger.error(f"{len(dup_voters)} VOTERS WITH DUPLICATE VOTES")
    logger.info(dup_voters)

    # Keep only last vote from each voter
    votes = votes.drop_duplicates(subset=[voter_col], keep="last")

    logger.success(f"{len(votes)} VOTES AFTER DEDUPLICATING")
    logger.info(votes)

    # Tally results
    team_votes = votes.groupby(team_col).size().reset_index(name="Total votes")
    team_votes = team_votes.sort_values(by="Total votes", ascending=False)
    team_votes = team_votes.reset_index(drop=True)
    team_votes.index = team_votes.index + 1

    logger.debug("-" * 88)
    logger.debug("FINAL TALLY")
    logger.info(team_votes)


if __name__ == "__main__":
    main()
