# Copy Training Data from Raspberry Pi to Laptop

Run these commands **on the laptop**, not inside an SSH session on the Pi.

- Raspberry Pi user: `throwing-a-mosfit`
- Raspberry Pi IP: `10.0.0.50`
- Remote folder: `/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data`
- Laptop destination: `/home/dan/throw-a-mosfit-pi2/training_data`

## Prepare destination

```bash
mkdir -p /home/dan/throw-a-mosfit-pi2/training_data
```

## Copy entire folder

Copies `training_data` and all subfolders into the laptop destination.

```bash
scp -r throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data /home/dan/throw-a-mosfit-pi2/
```

## Copy only folder contents

Copies everything directly inside `training_data`, without creating an extra nested `training_data` folder.

```bash
scp "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Copy only PNG images

```bash
scp "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*.png" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Copy only MP4 videos

```bash
scp "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*.mp4" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Copy PNG and MP4 files

```bash
scp "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*.{png,mp4}" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Copy files from the past hour

Copies top-level files modified within the last 60 minutes.

```bash
ssh throwing-a-mosfit@10.0.0.50 "find /home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data -maxdepth 1 -type f -mmin -60" | while read -r f; do
  scp "throwing-a-mosfit@10.0.0.50:$f" /home/dan/throw-a-mosfit-pi2/training_data/
done
```

## Copy files from the past 24 hours

Copies top-level files modified within the last 1,440 minutes.

```bash
ssh throwing-a-mosfit@10.0.0.50 "find /home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data -maxdepth 1 -type f -mmin -1440" | while read -r f; do
  scp "throwing-a-mosfit@10.0.0.50:$f" /home/dan/throw-a-mosfit-pi2/training_data/
done
```

## Copy files from the past 7 days

```bash
ssh throwing-a-mosfit@10.0.0.50 "find /home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data -maxdepth 1 -type f -mmin -10080" | while read -r f; do
  scp "throwing-a-mosfit@10.0.0.50:$f" /home/dan/throw-a-mosfit-pi2/training_data/
done
```

## Copy files from a specific date

For files named with `2026_10_31` in the filename:

```bash
scp "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*2026_10_31*" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Preserve timestamps and permissions

Add `-p` to retain original modification times and permissions.

```bash
scp -p "throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/*.png" /home/dan/throw-a-mosfit-pi2/training_data/
```

## Recommended: sync with rsync

Best for repeated transfers: copies only new or changed files and preserves timestamps, permissions, and folder structure.

```bash
rsync -av --progress \
  throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/ \
  /home/dan/throw-a-mosfit-pi2/training_data/
```

The trailing slash on the remote source means “copy the contents of this folder”; without it, `rsync` creates another `training_data` folder inside the destination. [67][70][73]

## Dry run before syncing

Preview what `rsync` would transfer without changing anything:

```bash
rsync -avn --progress \
  throwing-a-mosfit@10.0.0.50:/home/throwing-a-mosfit/throw-a-mosfit-pi2/training_data/ \
  /home/dan/throw-a-mosfit-pi2/training_data/
```