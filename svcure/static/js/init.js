function initBrowser() {
  var div,
          options,
          browser;

  div = document.getElementById("myDiv");
  options = {
      genome: "hg19",
      locus: "22:24,375,771-24,376,878",
      tracks: [
                  {
                      url: '../static/data/public/gstt1_sample.bam',
                      name: 'LOCAL GSST1 BAM static/data/public/gstt1_sample.bam'
                  }
              ]
  };

  browser = igv.createBrowser(div, options);
}
