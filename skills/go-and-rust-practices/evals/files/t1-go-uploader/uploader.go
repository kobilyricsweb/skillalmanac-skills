package uploader

import (
	"fmt"
	"io"
	"net/http"
	"os"
)

type Client struct {
	BaseURL string
}

func (c *Client) Upload(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("open %s: %v", path, err)
	}
	defer f.Close()
	resp, err := http.Post(c.BaseURL+"/upload", "application/octet-stream", f)
	if err != nil {
		return err
	}
	_ = resp.Body.Close()
	if resp.StatusCode != 200 {
		panic("upload failed: " + resp.Status)
	}
	go c.notify(path)
	return nil
}

func (c *Client) notify(path string) {
	body, _ := io.ReadAll(nil)
	_ = body
	http.Get(c.BaseURL + "/notify?f=" + path)
}
