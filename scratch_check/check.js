        () => {
            // Debug: log the page structure
            console.log("Debugging life.gov.sg page structure:");
            console.log("- #__next exists:", !!document.getElementById("__next"));
            console.log("- main element exists:", !!document.querySelector("main"));
            console.log("- section[role='main'] exists:", !!document.querySelector('section[role="main"]'));
            console.log("- All sections on page:", document.querySelectorAll("section").length);

            // life.gov.sg: extract from <section role="main"> or fallback to other section locations
            let mainSection = document.querySelector('section[role="main"]');

            // Fallback: try alternative XPath location
            if (!mainSection) {
                const xpath = '//*[@id="__next"]/div/main/section/div/section';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                mainSection = result.singleNodeValue;
                console.log("- Fallback XPath found section:", !!mainSection);
            }

            // Additional fallback: try just main > section
            if (!mainSection) {
                const main = document.querySelector('main');
                if (main) {
                    mainSection = main.querySelector('section');
                    console.log("- Found section in main:", !!mainSection);
                }
            }

            if (!mainSection) {
                console.log("No main section found, checking for article or div.main-content");
                const alternatives = document.querySelector('article') ||
                                    document.querySelector('div[role="main"]') ||
                                    document.querySelector('div.main-content') ||
                                    document.querySelector('main');
                return { mainSectionFound: false, alternatives: !!alternatives };
            }

            // Extract title from h1 or h2
            const titleEl = mainSection.querySelector('h1') || mainSection.querySelector('h2');
            const title = titleEl ? titleEl.textContent.trim() : null;

            // Extract description using XPath or fallback selectors
            let description = null;
            try {
                // Try specific XPath: //*[@id="__next"]/div/main/section[3]/div/div/h5
                const xpath = '//*[@id="__next"]/div/main/section[3]/div/div/h5';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const descEl = result.singleNodeValue;
                if (descEl) {
                    description = descEl.textContent.trim();
                }
            } catch (e) {
                // Fallback: look for h5 in various common locations
                const fallbackSelectors = [
                    'h5[class*="sidebar-description__Subtitle"]',
                    'div.sidebar_description__Subtitle h5',
                    'div.sidebar-description h5',
                    'main section h5'
                ];
                for (const selector of fallbackSelectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        description = el.textContent.trim();
                        break;
                    }
                }
            }

            // Extract content from paragraph using alternative XPath - handles multiple paragraphs
            let contentFromParagraph = null;
            try {
                // Try to extract all paragraphs from the content container
                const xpaths = [
                    '//*[@id="__next"]/div/main/section[2]/div/div/div[1]/p',
                    '//*[@id="__next"]/div/main/section/div/div/div/p'
                ];
                for (const xpath of xpaths) {
                    const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (result.snapshotLength > 0) {
                        const paragraphs = [];
                        for (let i = 0; i < result.snapshotLength; i++) {
                            const p = result.snapshotItem(i);
                            const text = p.textContent ? p.textContent.trim() : '';
                            if (text) {
                                paragraphs.push(text);
                            }
                        }
                        if (paragraphs.length > 0) {
                            contentFromParagraph = paragraphs.join('\n\n');
                            break;
                        }
                    }
                }
            } catch (e) {
                // If XPath extraction fails, continue without it
            }

            // Extract sidebar title if available
            const sidebarTitle = document.querySelector('div.sidebar-description__TItle');

            const sidebarMetadata = {
                title: sidebarTitle ? sidebarTitle.textContent.trim() : null,
                description: description
            };

            // Get all content from main section
            const contentHtml = mainSection.innerHTML;

            // Additional extraction: check for articles with multiple paragraphs in specific structure
            let contentByParagraphs = null;
            try {
                const xpath = '//*[@id="__next"]/div/main/section[2]/div/div/div[1]';
                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                const container = result.singleNodeValue;

                if (container) {
                    // Extract all paragraph elements from this container
                    const paragraphs = container.querySelectorAll('p');
                    if (paragraphs.length > 1) {
                        // Join multiple paragraphs with proper spacing
                        const texts = Array.from(paragraphs)
                            .map(p => (p.textContent || '').trim())
                            .filter(text => text.length > 0);
                        if (texts.length > 0) {
                            contentByParagraphs = texts.join('\n\n');
                        }
                    }
                }
            } catch (e) {
                // Continue without it
            }

            // Debug: log extracted content
            console.log("- Title found:", !!title, title ? title.substring(0, 50) : "");
            console.log("- Content HTML length:", contentHtml ? contentHtml.length : 0);
            console.log("- Paragraph content found:", !!contentFromParagraph);
            console.log("- Content by paragraphs found:", !!contentByParagraphs);

            return { title, contentHtml, sidebarMetadata, contentFromParagraph, contentByParagraphs };
        }
