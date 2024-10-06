const yaml = require("js-yaml");
const { DateTime } = require("luxon");
const syntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const htmlmin = require("html-minifier");
const markdownIt = require("markdown-it");
const markdownItAnchor = require("markdown-it-anchor");

module.exports = function (eleventyConfig) {
  // Disable automatic use of your .gitignore
  eleventyConfig.setUseGitIgnore(false);

  // Merge data instead of overriding
  eleventyConfig.setDataDeepMerge(true);

  // Custom function to create slug from filename or title
  function slugify(string) {
    return string
      .toString()
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^\w\-]+/g, "")
      .replace(/\-\-+/g, "-")
      .replace(/^-+/, "")
      .replace(/-+$/, "");
  }

  eleventyConfig.addFilter("slugify", slugify);

  // Add a new filter to strip date from filename
  eleventyConfig.addFilter("stripDate", (filename) => {
    return filename.replace(/^\d{4}-\d{2}-\d{2}-/, "");
  });

  // Add filters
  eleventyConfig.addFilter("limit", function (arr, limit) {
    return arr.slice(0, limit);
  });

  eleventyConfig.addFilter("dateToRfc3339", (dateObj) => {
    return DateTime.fromJSDate(dateObj, { zone: "utc" }).toISO();
  });

  eleventyConfig.addFilter("readableDate", (dateObj) => {
    return DateTime.fromJSDate(dateObj, { zone: "utc" }).toFormat(
      "dd LLL yyyy"
    );
  });

  // Add plugins
  eleventyConfig.addPlugin(syntaxHighlight);

  // Support .yaml Extension in _data
  eleventyConfig.addDataExtension("yaml", (contents) => yaml.load(contents));

  // Copy Static Files to /_site
  eleventyConfig.addPassthroughCopy({
    "./src/admin/config.yml": "./admin/config.yml",
    "./node_modules/alpinejs/dist/cdn.min.js": "./static/js/alpine.js",
    "./node_modules/prismjs/themes/prism-tomorrow.css":
      "./static/css/prism-tomorrow.css",
  });

  // Copy Image Folder to /_site
  eleventyConfig.addPassthroughCopy("./src/static/img");

  // Copy favicon to route of /_site
  eleventyConfig.addPassthroughCopy("./src/favicon.ico");

  // Customize Markdown Rendering
  let markdownLibrary = markdownIt({
    html: true,
    breaks: true,
    linkify: true,
  }).use(markdownItAnchor, {
    permalink: markdownItAnchor.permalink.ariaHidden({
      placement: "after",
      class: "direct-link",
      symbol: "#",
    }),
    level: [1, 2, 3, 4],
    slugify: eleventyConfig.getFilter("slugify"),
  });
  eleventyConfig.setLibrary("md", markdownLibrary);

  // Updated collection for all content (posts and links)
  eleventyConfig.addCollection("allContent", function (collectionApi) {
    return collectionApi
      .getFilteredByGlob("src/content/**/*.md")
      .map((item) => {
        const slug = item.data.title
          ? slugify(item.data.title)
          : slugify(item.fileSlug.replace(/^\d{4}-\d{2}-\d{2}-/, ""));

        // Determine if it's a post or a link based on the date
        const isPost = /^\d{4}-\d{2}-\d{2}/.test(item.fileSlug);

        // Set permalink based on content type
        item.data.permalink = isPost ? `/${slug}/` : `/links/${slug}/`;
        item.data.contentType = isPost ? "post" : "link";

        item.url = item.data.permalink;
        return item;
      })
      .sort((a, b) => b.date - a.date);
  });

  // Separate collections for posts and links
  eleventyConfig.addCollection("posts", (collectionApi) => {
    return collectionApi
      .getFilteredByGlob("src/content/**/*.md")
      .filter((item) => item.data.contentType === "post");
  });

  eleventyConfig.addCollection("links", (collectionApi) => {
    return collectionApi
      .getFilteredByGlob("src/content/**/*.md")
      .filter((item) => item.data.contentType === "link");
  });

  // Minify HTML
  eleventyConfig.addTransform("htmlmin", function (content, outputPath) {
    if (outputPath && outputPath.endsWith(".html")) {
      let minified = htmlmin.minify(content, {
        useShortDoctype: true,
        removeComments: true,
        collapseWhitespace: true,
      });
      return minified;
    }
    return content;
  });

  // Add a shortcode for rendering the current year
  eleventyConfig.addShortcode("year", () => `${new Date().getFullYear()}`);

  // Configuration
  return {
    dir: {
      input: "src",
      includes: "_includes",
      data: "_data",
      output: "_site",
    },
    templateFormats: ["html", "njk", "md", "11ty.js"],
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    dataTemplateEngine: "njk",
  };
};
