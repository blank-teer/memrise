package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
)

func main() {
	csvFile, err := os.Open("data/init/text/raw.csv")
	if err != nil {
		log.Fatal(err)
	}

	reader := csv.NewReader(csvFile)

	rows, err := reader.ReadAll()
	if err != nil {
		log.Fatal(err)
	}

	files, err := ioutil.ReadDir("data/init/audio")
	if err != nil {
		log.Fatal()
	}

	filtered := make([][]string, 0, len(rows))
LOOP:
	for _, row := range rows[1:] {
		csvPos := row[0]
		csvWrd := row[1]

		for _, file := range files {
			fileWrd := strings.Split(file.Name(), ".")[1]

			if fileWrd == csvWrd {
				continue LOOP
			}
		}
		filtered = append(filtered, []string{csvPos, csvWrd})
	}

	delay := 2 * time.Second

	for _, row := range filtered {
		pos := row[0]
		wrd := row[1]

		fmt.Println("pos:", pos)
		fmt.Println("wrd:", wrd)

		filename := fmt.Sprintf("data/init/audio/%s.%s.mp3", pos, wrd)
		f, err := os.Create(filename)
		if err != nil {
			log.Fatal(err)
		}

		url := fmt.Sprintf("https://wooordhunt.ru/data/sound/word/us/mp3/%s.mp3", wrd)
		r, err := http.DefaultClient.Get(url)
		if err != nil {
			log.Fatal(err)
		}

		_, err = io.Copy(f, r.Body)
		if err != nil {
			log.Fatal(err)
		}

		fmt.Printf("sts: done\n\n")

		time.Sleep(delay)
	}
}
